"""
A simple AI Action template for retrieving Wikipedia article summary

Please check out the base guidance on AI Actions in our main repository readme:
https://github.com/sema4ai/actions/blob/master/README.md

"""

import os

from robocorp import browser
from sema4ai.actions import Response, action

HEADLESS_BROWSER = not os.getenv("HEADLESS_BROWSER")


@action
def get_wikipedia_article_summary(article_url: str) -> Response[str]:
    """
    Retrieves the summary (first paragraph) of given Wikipedia article.

    Args:
        article_url: URL of the article to get the summary of.

    Returns:
        Summary of the article.
    """

    browser.configure(browser_engine="chromium", headless=HEADLESS_BROWSER)

    page = browser.goto(article_url)

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("networkidle")

    paragraphs = page.query_selector_all(".mw-content-ltr>p:not(.mw-empty-elt)")
    summary = paragraphs[0].inner_text()

    # Pretty print for log
    print(summary)

    return Response(result=summary)
