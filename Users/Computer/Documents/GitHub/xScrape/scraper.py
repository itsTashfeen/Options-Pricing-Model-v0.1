from playwright.sync_api import sync_playwright
import random
import time
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional
from pathlib import Path
from .proxy_manager import ProxyManager

class TwitterScraper:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36",
        ]
        self.setup_logging()
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "scraper.log"),
                logging.StreamHandler()
            ]
        )

    def simulate_human_scroll(self, page) -> None:
        try:
            scroll_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.viewport_size["height"]
            current_position = 0

            while current_position < scroll_height:
                scroll_distance = random.randint(100, 500)
                current_position += scroll_distance
                
                # Smooth scroll with random duration
                page.evaluate(f"""
                    window.scrollBy({{
                        top: {scroll_distance},
                        behavior: 'smooth'
                    }});
                """)
                
                # Random pause between scrolls
                time.sleep(random.uniform(1, 3))
                
                # Simulate reading pause
                if random.random() < 0.2:
                    time.sleep(random.uniform(2, 5))

        except Exception as e:
            logging.error(f"Error during scrolling: {str(e)}")
            raise

    def extract_tweet_data(self, tweet_element) -> Dict:
        try:
            return {
                "text": tweet_element.evaluate('element => element.querySelector("[data-testid="tweetText"]")?.textContent || ""'),
                "timestamp": tweet_element.evaluate('element => element.querySelector("time")?.dateTime || ""'),
                "likes": tweet_element.evaluate('element => element.querySelector("[data-testid="like"]")?.textContent || "0"'),
                "retweets": tweet_element.evaluate('element => element.querySelector("[data-testid="retweet"]")?.textContent || "0"'),
                "replies": tweet_element.evaluate('element => element.querySelector("[data-testid="reply"]")?.textContent || "0"'),
            }
        except Exception as e:
            logging.error(f"Error extracting tweet data: {str(e)}")
            return {}

    def scrape_profile(self, username: str, tweet_limit: Optional[int] = 100) -> List[Dict]:
        tweets = []
        
        with sync_playwright() as p:
            try:
                proxy = self.proxy_manager.get_proxy()
                browser = p.chromium.launch(
                    proxy=proxy,
                    headless=True
                )
                
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=random.choice(self.user_agents)
                )
                
                page = context.new_page()
                
                # Add random delays to network requests
                page.route("**/*", lambda route: route.continue_(
                    delay=random.randint(100, 1000)
                ))
                
                page.goto(f"https://twitter.com/{username}")
                time.sleep(random.uniform(2, 4))
                
                tweets_seen = 0
                while len(tweets) < tweet_limit:
                    self.simulate_human_scroll(page)
                    
                    tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
                    
                    for tweet in tweet_elements[tweets_seen:]:
                        tweet_data = self.extract_tweet_data(tweet)
                        if tweet_data:
                            tweets.append(tweet_data)
                        
                        if len(tweets) >= tweet_limit:
                            break
                    
                    tweets_seen = len(tweet_elements)
                    
                    if page.query_selector("div[data-testid='noMoreItems']"):
                        break

            except Exception as e:
                logging.error(f"Error scraping profile {username}: {str(e)}")
                raise
            finally:
                if 'browser' in locals():
                    browser.close()

        return tweets

    def save_tweets(self, tweets: List[Dict], username: str) -> None:
        filename = self.output_dir / f"tweets_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(tweets)} tweets to {filename}")
        except Exception as e:
            logging.error(f"Error saving tweets: {str(e)}")
            raise