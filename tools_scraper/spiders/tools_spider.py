from pathlib import Path

import scrapy

DATA_PATH: Path = Path("./data/tools")
BASE_URL = "https://oecd.ai/en/catalogue/tools?page=1"

class ToolsSpider(scrapy.Spider):
    name = "tools"
    start_urls = [
        BASE_URL,
    ]

    def parse(self, response, **kwargs):
        pages_path = DATA_PATH / "pages/"
        pages_path.mkdir(parents=True, exist_ok=True)
        pages_path.joinpath(f"{response.url.split('/')[-1]}.html").write_bytes(response.body)

        yield from response.follow_all(css="app-tool-card h2 a", callback=self.parse_tool)

        if response.url == BASE_URL:  # we only need to check for all pages on the first page
            last_page = int(response.css("a.pagination-link::text").getall()[-1])
            last_page = 1  # DEBUG
            all_pages = [BASE_URL[:-1] + str(page) for page in range(2, last_page + 1)]  # reconstruct page URLs
            yield from response.follow_all(all_pages, callback=self.parse)

    def parse_tool(self, response):
        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def extract_all_with_css(query):
            return [part.replace("\xa0", " ") for part in response.css(query).getall()]

        def extract_about_tool() -> dict[str, list[str]]:
            sections = response.css("div.card div.is-flex")
            about = {}
            for section in sections:
                key = section.css("p::text").get(default='').strip().rstrip(":")
                values = [value.strip() for value in section.css("li ::text").getall()]
                about[key] = values
            return about

        def extract_taxonomy_list() -> dict[str, list[str]]:
            response.css("span.icon-text div.is-flex i.icon")
            response.css("span.icon-text div.is-flex a::text")

        tools_path = DATA_PATH / "tools/"
        tools_path.mkdir(parents=True, exist_ok=True)
        tools_path.joinpath(f"{response.url.split('/')[-1]}.html").write_bytes(response.body)

        yield {
            'name': extract_with_css('h2.title::text'),
            'url': response.url,
            'uploaded_date': extract_with_css('span.content::text').replace("Uploaded on ", ""),
            'organisation': extract_with_css('div.column.is-8 span.country-label::text'),
            'text': "".join(extract_all_with_css('.is-8 > div:nth-child(7) ::text')),
            **extract_about_tool()
        }

