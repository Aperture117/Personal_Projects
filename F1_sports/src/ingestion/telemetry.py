import pandas as pd
import fastf1
from src.config import RAW_DATA_DIR
from src.utils.logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = get_logger(__name__)

class TelemetryIngestion:
    def __init__(self):
        self.cache_dir = RAW_DATA_DIR / "fastf1_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(self.cache_dir))

    def _process_single_lap(self, lap):
        try:
            tel = lap.get_telemetry()
            if tel.empty: return None
            tel['Driver'] = lap['Driver']
            tel['LapNumber'] = lap['LapNumber']
            tel['Compound'] = lap['Compound']
            tel['TyreLife'] = lap['TyreLife']
            tel['LapTime'] = lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None
            return tel
        except:
            return None

    def fetch_session_data(self, year=2024, race='Bahrain', session_type='R', progress_callback=None):
        logger.info(f"Fetching F1 telemetry for {year} {race} {session_type}...")
        try:
            session = fastf1.get_session(year, race, session_type)
            session.load(telemetry=True, laps=True, weather=True)
            
            # 1. Extract Circuit Shape for the Map
            fastest_lap = session.laps.pick_fastest()
            circuit_telemetry = fastest_lap.get_telemetry().filter(items=['X', 'Y'])
            
            laps = session.laps
            total_laps = len(laps)
            all_telemetry = []
            
            # 2. Parallel Telemetry Retrieval
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(self._process_single_lap, lap): i for i, lap in laps.iterrows()}
                completed = 0
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None: all_telemetry.append(result)
                    completed += 1
                    if progress_callback and completed % 20 == 0:
                        progress_callback(completed, total_laps, f"Syncing Telemetry: {completed}/{total_laps}")
            
            combined_df = pd.concat(all_telemetry, ignore_index=True)
            
            # 3. Create ML training set
            ml_df = combined_df.groupby(['Driver', 'LapNumber']).agg({
                'LapTime': 'first',
                'TyreLife': 'first',
                'Compound': 'first',
                'Speed': 'mean'
            }).reset_index()
            
            # Filenames
            base_name = f"{year}_{race}_{session_type}"
            full_path = RAW_DATA_DIR / f"{base_name}_full.parquet"
            ml_path = RAW_DATA_DIR / f"{base_name}_laps.parquet"
            track_path = RAW_DATA_DIR / f"{base_name}_circuit.parquet"
            
            # Clean timedeltas
            for df in [combined_df, ml_df]:
                for col in df.select_dtypes(include=['timedelta64[ns]']).columns:
                    df[col] = df[col].dt.total_seconds()

            # Save All
            combined_df.to_parquet(full_path, engine='fastparquet')
            ml_df.to_parquet(ml_path, engine='fastparquet')
            circuit_telemetry.to_parquet(track_path, engine='fastparquet')
            
            logger.info(f"Ingestion complete. Track map and ML sets saved.")
            return ml_path
            
        except Exception as e:
            logger.error(f"Error fetching telemetry: {e}")
            return None
