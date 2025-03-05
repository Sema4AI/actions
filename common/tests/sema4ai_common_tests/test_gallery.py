example_metadata = {
    "packages": {
        "Google Docs": {
            "name": "Google Docs",
            "versions": [
                {
                    "version": "1.2.0",
                    "description": "Pre-built AI actions to read Google documents in Markdown format",
                    "zip": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.0/google-docs.zip",
                    "icon": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.0/package.png",
                    "metadata": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.0/metadata.json",
                    "readme": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.0/README.md",
                    "changelog": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.0/CHANGELOG.md",
                    "actions": [
                        {
                            "name": "Get Document By Name",
                            "description": "Get a Google Document by its name.\nIf multiple documents with the same name are found,\nyou need to use the ID of the document to load it.\nHint: Copy-pasting the URL of the document in the Agent will allow it to fetch the document by ID\n\nApostrophes in the title need to be escaped with a backslash.\nThe result is the Document formatted using the Extended Markdown Syntax.",
                        },
                        {
                            "name": "Get Document By Id",
                            "description": "Get a Google Document by its ID. The result is the Document formatted using the Extended Markdown Syntax.",
                        },
                        {
                            "name": "Create Document",
                            "description": "Create a new Google Document from an Extended Markdown string.\nArgs:\n    title: The Google Document title\n    body: The Google Document body as an Extended Markdown string.\n    oauth_access_token: The OAuth2 Google access token",
                        },
                    ],
                    "python_env_hash": "37b641566bce9802",
                    "zip_hash": "28de4f44229a5a620aab16b1310fff0a896cd65130a719318c14932922349cdf",
                },
                {
                    "version": "1.2.1",
                    "description": "Get contents of Google Docs as Markdown",
                    "zip": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.1/google-docs.zip",
                    "icon": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.1/package.png",
                    "metadata": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.1/metadata.json",
                    "readme": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.1/README.md",
                    "changelog": "https://cdn.sema4.ai/gallery/actions/google-docs/1.2.1/CHANGELOG.md",
                    "actions": [
                        {
                            "name": "Get Document By Name",
                            "description": "Get a Google Document by its name.\nIf multiple documents with the same name are found,\nyou need to use the ID of the document to load it.\nHint: Copy-pasting the URL of the document in the Agent will allow it to fetch the document by ID\n\nApostrophes in the title need to be escaped with a backslash.\nThe result is the Document formatted using the Extended Markdown Syntax.",
                        },
                        {
                            "name": "Get Document By Id",
                            "description": "Get a Google Document by its ID. The result is the Document formatted using the Extended Markdown Syntax.",
                        },
                        {
                            "name": "Create Document",
                            "description": "Create a new Google Document from an Extended Markdown string.\nArgs:\n    title: The Google Document title\n    body: The Google Document body as an Extended Markdown string.\n    oauth_access_token: The OAuth2 Google access token",
                        },
                    ],
                    "python_env_hash": "37b641566bce9802",
                    "zip_hash": "bfbf4be81de66665c5707fe48806925e2718d2bdddbf77c0b2d3a073d05fec34",
                },
            ],
        }
    }
}


def test_import_gallery_action_packages(data_regression, tmpdir):
    import os
    from pathlib import Path

    from sema4ai.common.gallery import GalleryActionPackages

    gallery_actions = GalleryActionPackages(example_metadata)
    found = gallery_actions.list_packages()
    data_regression.check(found.as_dict())

    assert "Google Docs 1.2.0" in found.result
    target = Path(tmpdir) / "download"
    result = gallery_actions.extract_package("Google Docs 1.2.0", target)
    assert result.success, f"Expected success. Error message: {result.message}"

    extracted_to = target / "google-docs"
    assert extracted_to.samefile(Path(result.result))
    assert extracted_to.exists(), f"Extracted dir: {extracted_to} does not exist"
    assert {
        ".gitignore",
        "actions.py",
        "CHANGELOG.md",
        "LICENSE",
        "package.png",
        "package.yaml",
        "README.md",
    }.issubset(set(os.listdir(extracted_to)))
