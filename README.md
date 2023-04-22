# OECD scraper

Simple scrapy scraper to download and extract information from the Catalogue of Tools & Metrics for Trustworthy AI by
the OECD ([link](https://oecd.ai/en/catalogue/tools?terms=&page=1)). 

## Installation
To install the project dependencies run:

```shell
conda create --name <envname> --file requirements.txt
```

## Running scrapy
To run the scraper you have to call scrapy from the command line:

```shell
scrapy crawl tools
```

The scraper will automatically save the html pages in a separate data directory.
If you want to capture the data extracted by scrapy you need to add an additional argument:

```shell
scrapy crawl tools -O tools.jsonl
```