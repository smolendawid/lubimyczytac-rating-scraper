import asyncio
from playwright.async_api import async_playwright

# Constants
URL = 'https://lubimyczytac.pl/'
TITLES_FILE = 'titles.txt'
COOKIE_BUTTON_SELECTOR = '#onetrust-accept-btn-handler'
SEARCH_INPUT_SELECTOR = 'input[name="phrase"]'
RATING_SELECTOR = 'span.listLibrary__ratingStarsNumber'
RESULTS = {}
SLEEP_TIME = 2

# Helper Functions
def parse_string_to_float(s):
    """Parse a string, handle commas, and convert to float."""
    s = s.strip().replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def read_titles_from_file(filename):
    """Read titles from the specified file and return them as a list."""
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

async def accept_cookies(page):
    """Accept cookies if the button is available."""
    try:
        await page.wait_for_selector(COOKIE_BUTTON_SELECTOR)
        await page.click(COOKIE_BUTTON_SELECTOR)
    except Exception as e:
        print(f"Error accepting cookies: {e}")

async def perform_search(page, title):
    """Perform the search for the given title."""
    await page.fill(SEARCH_INPUT_SELECTOR, title)
    await page.keyboard.press('Enter')

    # Wait for a short while to ensure the page is loaded
    await asyncio.sleep(SLEEP_TIME)

async def get_rating(page, title):
    """Retrieve the rating from the first search result using the general class selector."""
    try:
        # Select the first rating element found with the generic selector
        rating_element = await page.query_selector(RATING_SELECTOR)
        if rating_element:
            rating = await rating_element.text_content()
            rating_number = parse_string_to_float(rating)
            RESULTS[title] = rating_number
            print(f'Title: {title} - Rating: {rating}')
        else:
            print(f'No rating found for: {title}')
            RESULTS[title] = None
    except Exception as e:
        print(f'Could not find rating for: {title}, error: {e}')

async def search_titles():
    """Main function to manage searching for titles and collecting ratings."""
    titles = read_titles_from_file(TITLES_FILE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(URL)

        # Accept cookies if it's the first iteration
        if titles:
            await accept_cookies(page)

        for title in titles:
            try:
                await perform_search(page, title)
                await get_rating(page, title)
                # Try again if failed
                if title not in RESULTS:
                    await get_rating(page, title)
                await page.goto(URL)  # Go back to the homepage for the next search
            except: 
                print("FAILED")

        await browser.close()

    display_sorted_results()

def display_sorted_results():
    """Sort and display the results based on the rating."""
    sorted_results = sorted(
        (item for item in RESULTS.items() if item[1] is not None),
        key=lambda x: x[1], reverse=True
    )
    
    print("\nSorted Results by Rating (Highest First):")
    for title, rating in sorted_results:
        print(f'{title}: {rating}')

# Run the async function
if __name__ == "__main__":
    asyncio.run(search_titles())
