from datetime import datetime
from pathlib import Path

import scrapy
from scrapy import Selector

DATA_PATH: Path = Path("./data/tools")
BASE_URL = "https://oecd.ai/en/catalogue/tools?page=1"
ICON_TO_TAXONOMY = {
    "icon-TopicsRelatedtotheResults": "related",
    "icon-Public": "country",
}


def convert_date(date: str) -> str:
    """Converts date from 'Month day, year' to ISO-8601 format, e.g. Apr 30, 2023 to 2023-04-30"""
    return datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")


class ToolsSpider(scrapy.Spider):
    name = "tools"
    start_urls = [
        BASE_URL,
    ]

    def parse(self, response, **kwargs):
        """Scrapy will start crawling with this method. We use this method to traverse the pages and call the
        parse_tool method to scrape individual tool pages"""
        # Store the files
        pages_path: Path = DATA_PATH / "pages/"
        pages_path.mkdir(parents=True, exist_ok=True)
        pages_path.joinpath(f"{response.url.split('/')[-1]}.html").write_bytes(response.body)

        # Check every tool listed on the page
        yield from response.follow_all(css="app-tool-card h2 a", callback=self.parse_tool)

        # Find all page URLs and add them to our crawl
        if response.url == BASE_URL:  # we only need to check for all pages on the first page
            last_page = int(response.css("a.pagination-link::text").getall()[-1])
            all_pages = [BASE_URL[:-1] + str(page) for page in range(2, last_page + 1)]  # reconstruct page URLs
            yield from response.follow_all(all_pages, callback=self.parse)

    def parse_tool(self, response):
        """Method to scrape individual tool pages."""

        def extract_with_css(base: Selector, query: str) -> str:
            return base.css(query).get(default="").strip().replace("\xa0", " ")

        def extract_all_with_css(base: Selector, query: str) -> list[str]:
            return [part.replace("\xa0", " ") for part in base.css(query).getall()]

        def extract_about_tool(base: Selector) -> dict[str, list[str]]:
            sections = base.css("div.card div.is-flex")
            about = {}
            for section in sections:
                key = section.css("p::text").get(default="").strip().rstrip(":")
                values = [value.strip() for value in section.css("li ::text").getall()]
                about[key] = values
            return about

        def extract_taxonomy_list(base: Selector) -> dict[str, list[str]]:
            icons = base.css(".icon-text div")

            taxonomy = {"related": [], "country": []}
            for icon in icons:
                key = icon.css("i.icon").xpath("@class").extract()
                if not key:  # if country is empty, the page will have an empty div
                    continue
                key = key[0].split()[1]
                key = ICON_TO_TAXONOMY.get(key, key)
                taxonomy[key] = [string.strip() for string in extract_all_with_css(icon, "::text")]
            return taxonomy

        def extract_badges_list(base: Selector) -> dict[str, list[str]]:
            badge_names = base.css(".field span::text").getall()
            badge_links = base.css(".field a::attr(href)").getall()
            return {name: link for name, link in zip(badge_names, badge_links)}

        # Store the files
        tools_path = DATA_PATH / "tools/"
        tools_path.mkdir(parents=True, exist_ok=True)
        tools_path.joinpath(f"{response.url.split('/')[-1]}.html").write_bytes(response.body)

        yield {
            "name": extract_with_css(response, "h2.title::text"),
            "url": response.url,
            **extract_badges_list(response),
            **extract_taxonomy_list(response),
            "uploaded_date": convert_date(extract_with_css(response, ".content::text").replace("Uploaded on ", "")),
            "organisation": extract_with_css(response, ".is-8 span.country-label::text"),
            "text": "\n".join(extract_all_with_css(response.css(".is-8 > div")[-1], "::text")),  # only use top lvl divs
            **extract_about_tool(response),
        }
