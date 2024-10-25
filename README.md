# Desafio Quero Passagem!

Este é a minha resolução do desafio técnico da Quero Passagem.

Como soluções eu propus, primeiramente uma análise cuidadosa do site que buscavamos extrair os dados e, então
a partir daí, montar uma solução estratégica que extrai esses dados através da API que o site utiliza e, utilizando BeautifulSoup
conseguimos extrair e autenticar nosso cliente (python.requests) com a Api da plataforma.

Além disso, para garantir uma solução técnica diferente, também montei um crawler bastante simples em selenium que extrai (de forma mais lenta
porém consistente) os dados do mesmo site. (Este modelo releva a quantidade de poltronas, já que é um dado que pode ser directamente obtido pela API que conseguimos o acesso anteriormente.

Para mais informações no processo de escrita e design da solução, [recomendo a leitura do PDF com os detalhes](https://github.com/BrunoMarinhoM/Desafio-Quero-Passagem/blob/main/Teste%20Quero%20Passagem.pdf)

Por fim, para excecutar o crawl, basta-nos:

```
pip install -r requirements.txt
python crawl_from...
```

Com um dos dois arquivos principais o crawl_from_website.py que irá utilizar o selenium e será um pouco mais lento
e o crawl_from_api.py que irá autenticar-se e extrair os dados da api.

:)
