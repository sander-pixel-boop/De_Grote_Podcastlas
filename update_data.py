import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim
import time
import os

# Set up geocoder
geolocator = Nominatim(user_agent="podcastlas_scraper")

def get_location(name, category):
    try:
        # Give context for geocoding based on category to improve accuracy
        if category == "Provincie":
            query = f"{name}, Belgium" if name in ["Henegouwen", "Luik", "Antwerpen", "Namen", "West-Vlaanderen", "Oost-Vlaanderen", "Limburg", "Vlaams-Brabant", "Waals-Brabant"] else f"{name}, Netherlands"
        else:
            query = name

        location = geolocator.geocode(query, timeout=10, language='nl')
        if location:
            return location.latitude, location.longitude

        # If not found, try just the name
        time.sleep(1)
        location = geolocator.geocode(name, timeout=10, language='en')
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Error geocoding {name}: {e}")

    return None, None

def determine_kaartweergave(category):
    if category in ["Reguliere aflevering", "Werelddeel", "Eilanden", "Rafelrandjes", "Kids"]:
        return "Land"
    elif category in ["Provincie", "Wereldstad", "Special"]:
        return "Punt"
    return "Land" # Default

def scrape_episodes():
    csv_file = "data.csv"
    if os.path.exists(csv_file):
        existing_df = pd.read_csv(csv_file)
        existing_df.columns = existing_df.columns.str.strip()
        existing_names = set(existing_df['Weergave_Naam'].tolist())
    else:
        existing_df = pd.DataFrame()
        existing_names = set()

    new_episodes = []
    page = 1

    while True:
        url = f'https://www.grotepodcastlas.nl/afleveringen?6b564bc9_page={page}'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('div', class_='afleveringen-item')

        if not items:
            break

        print(f"Processing page {page} with {len(items)} items")

        for item in items:
            title_div = item.find('div', class_='afleveringen-item-titel')
            if not title_div:
                continue

            title = title_div.text.strip()

            if title in existing_names:
                continue # Already in our data

            print(f"Found new episode: {title}")

            link_tag = item.find('a', class_='afleveringen-item-wrapper')
            link = "https://www.grotepodcastlas.nl" + link_tag['href'] if link_tag else None

            number_wrappers = item.find_all('div', class_='afleveringen-item-number')
            number = "0"
            for n in number_wrappers:
                text = n.text.strip()
                if text.isdigit():
                    number = text

            category = "Reguliere aflevering"
            all_text = item.text.replace('\n', ' ')

            if "Provincie" in all_text:
                category = "Provincie"
            elif "Wereldstad" in all_text:
                category = "Wereldstad"
            elif "Rafelrandjes" in all_text:
                category = "Rafelrandjes"
            elif "Special" in all_text:
                category = "Special"
            elif "Werelddeel" in all_text:
                category = "Werelddeel"
            elif "Eilanden" in all_text:
                category = "Eilanden"
            elif "Kids" in all_text:
                category = "Kids"

            episode_label = f"Afl. {number}" if category == "Reguliere aflevering" else f"{category} {number}"
            kaartweergave = determine_kaartweergave(category)

            lat, lon = get_location(title, category)

            new_episode = {
                'Weergave_Naam': title,
                'Locatie': title, # Could be improved if there was a way to map Dutch to English names consistently, but using title is mostly fine as map works with English/Dutch names often
                'Kaartweergave': kaartweergave,
                'Categorie': category,
                'Aflevering': episode_label,
                'Waarde': 1,
                'Latitude': lat if lat is not None else "",
                'Longitude': lon if lon is not None else "",
                'Link': link
            }

            new_episodes.append(new_episode)
            existing_names.add(title) # Add to prevent duplicates within same run
            time.sleep(1) # Be nice to the geocoding service

        next_btn = soup.find('a', class_='w-pagination-next')
        if not next_btn and len(items) < 100:
            # Maybe there are fewer items on the last page. In Webflow, next button class determines pagination
            pass

        page += 1

        # Simple safety check to prevent infinite loops if something goes wrong with pagination parsing
        if page > 100:
            break

    if new_episodes:
        new_df = pd.DataFrame(new_episodes)

        if not existing_df.empty:
            # Match columns
            new_df = new_df[existing_df.columns]

            # The original data.csv seems to be appended at the end or reversed, let's just append new at the bottom
            # Actually since they are ordered chronologically it doesn't matter too much,
            # wait, if Colombia is at top and it's episode 1, we should append new episodes at the BOTTOM.
            # But the pagination is newest first (page 1 is newest).
            # So we should reverse `new_episodes` before appending if we want them at the bottom.
            # However, `existing_df` has old episodes at top and new at bottom.
            # Wait, `new_episodes` is currently populated with newest first (from page 1).
            # So if we concat `[existing_df, new_df_reversed]` we get chronological order.

            # Let's just prepend them for now, it's easier to find newest if they are at top.
            # Let's concatenate `new_df` and `existing_df` (new on top). The Streamlit app doesn't care.

            updated_df = pd.concat([new_df, existing_df], ignore_index=True)
            updated_df.to_csv(csv_file, index=False)
            print(f"Added {len(new_episodes)} new episodes to {csv_file}")
        else:
            new_df.to_csv(csv_file, index=False)
            print(f"Created {csv_file} with {len(new_episodes)} episodes")
    else:
        print("No new episodes found.")

if __name__ == "__main__":
    scrape_episodes()
