import pandas as pd
import fastf1
from src.config import RAW_DATA_DIR
from src.utils.logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = get_logger(__name__)

class TelemetryIngestion:
    """
    Handles fetching telemetry, timing, and weather data.
    Saves outputs as parquet files for the downstream prediction and LLM pipelines.
    Optimized with parallel processing.
    """
    def __init__(self):
        # Enable FastF1 caching locally to speed up iterations and avoid API limits
        self.cache_dir = RAW_DATA_DIR / "fastf1_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(self.cache_dir))

    def _process_single_lap(self, lap):
        """Helper to process telemetry for a single lap."""
        try:
            tel = lap.get_telemetry()
            if tel.empty:
                return None
                
            tel['Driver'] = lap['Driver']
            tel['LapNumber'] = lap['LapNumber']
            tel['Compound'] = lap['Compound']
            tel['TyreLife'] = lap['TyreLife']
            tel['LapTime'] = lap['LapTime']  # Explicitly save the official lap time
            return tel
        except Exception as e:
            logger.error(f"Error processing lap {lap['LapNumber']} for {lap['Driver']}: {e}")
            return None

    def fetch_session_data(self, year=2024, race='Bahrain', session_type='R', progress_callback=None):
        """
        Fetches telemetry data for a specified session using parallel processing.
        """
        logger.info(f"Fetching F1 telemetry for {year} {race} {session_type}...")
        try:
            session = fastf1.get_session(year, race, session_type)
            session.load(telemetry=True, laps=True, weather=True)
            
            laps = session.laps
            total_laps = len(laps)
            all_telemetry = []
            
            logger.info(f"Parallelizing processing for {total_laps} laps...")
            
            # Use ThreadPoolExecutor for concurrent telemetry retrieval
            # This balances between I/O (API calls/cache reads) and CPU (interpolation)
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(self._process_single_lap, lap): i for i, lap in laps.iterrows()}
                
                completed = 0
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        all_telemetry.append(result)
                    
                    completed += 1
                    if progress_callback and completed % 5 == 0: # Update UI every 5 laps to reduce flicker
                        progress_callback(completed, total_laps, f"Processing {completed}/{total_laps} Lap Telemetry...")
                
            if progress_callback:
                progress_callback(total_laps, total_laps, "Optimizing and saving data...")
                
            combined_df = pd.concat(all_telemetry, ignore_index=True)
            
            # Save as parquet
            output_path = RAW_DATA_DIR / f"{year}_{race}_{session_type}_laps.parquet"
            
            # Data cleaning for serialization
            for col in combined_df.select_dtypes(include=['timedelta64[ns]']).columns:
                combined_df[col] = combined_df[col].dt.total_seconds()
                
            combined_df = combined_df.map(lambda x: str(x) if isinstance(x, list) or isinstance(x, dict) else x)
            
            combined_df.to_parquet(output_path, engine='fastparquet')
            logger.info(f"Parallel processing complete. Saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error fetching telemetry: {e}")
            return None
