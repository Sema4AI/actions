def test_slugify():
    from sema4ai.common.text import slugify

    assert slugify("ação", allow_unicode=True) == "ação"
    assert slugify("ação", allow_unicode=False) == "acao"
    assert slugify("ação /?*Σ 22", allow_unicode=False) == "acao-22"
