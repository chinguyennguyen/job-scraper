from datetime import datetime
from config import cfg
from scraper import scrape_city
from storage import init_db, save_jobs, get_stats, age_unreviewed
import pandas as pd


def main():
    init_db()  # creates jobs.db if it doesn't exist yet
    age_unreviewed()
    
    print(f"Job scraper started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Search terms: {len(cfg['search_terms'])} terms")
    print(f"Cities: {', '.join(c['location'] for c in cfg['cities'])}")

    city_results = []
    for city_config in cfg["cities"]:
        result = scrape_city(city_config)
        if result is not None:
            city_results.append(result)

    if not city_results:
        print("\nNo results from any city. Exiting.")
        return

    df_all = pd.concat(city_results, ignore_index=True)
    save_jobs(df_all)

    stats = get_stats()
    print(f"Applied           : {stats['applied']}")
    print(f"In progress       : {stats['in_progress']}")
    print(f"Rejected          : {stats['rejected']}")


if __name__ == "__main__":
    main()
