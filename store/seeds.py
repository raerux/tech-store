from .models import Category, Product

def run_seed():
    cat_eletronicos, _ = Category.objects.get_or_create(nome="Eletrônicos")
    cat_roupas, _ = Category.objects.get_or_create(nome="Roupas")
    cat_livros, _ = Category.objects.get_or_create(nome="Livros")

    products = [
        {
            "nome": "Notebook Pro X",
            "descricao": "Notebook potente para desenvolvimento e jogos.",
            "preco": 5999.90,
            "imagem_url": "https://picsum.photos/400/300?1",
            "estoque": 15,
            "destaque": True,
            "categoria": cat_eletronicos
        },
        {
            "nome": "Mouse Gamer RGB",
            "descricao": "Mouse ergonômico com alta precisão.",
            "preco": 249.90,
            "imagem_url": "https://picsum.photos/400/300?2",
            "estoque": 50,
            "destaque": True,
            "categoria": cat_eletronicos
        },
        {
            "nome": "Camiseta Tech",
            "descricao": "Camiseta confortável com estampa geek.",
            "preco": 79.90,
            "imagem_url": "https://picsum.photos/400/300?3",
            "estoque": 100,
            "destaque": False,
            "categoria": cat_roupas
        },
        {
            "nome": "Livro Clean Code",
            "descricao": "Boas práticas para escrita de código limpo.",
            "preco": 129.90,
            "imagem_url": "https://picsum.photos/400/300?4",
            "estoque": 30,
            "destaque": True,
            "categoria": cat_livros
        }
    ]

    for p in products:
        Product.objects.get_or_create(nome=p["nome"], defaults=p)