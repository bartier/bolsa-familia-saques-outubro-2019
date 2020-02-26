# Bolsa Família Saques - Outubro/19

Esse projeto tem como objetivo utilizar a `Elastic Stack` para a visualização
dos dados dos saques realizados no mês de Outubro/19 do Bolsa Família.

## Obtenção dos dados

Os dados para serem processados foram obtidos no  [Portal Brasileiro de Dados Abertos](http://www.dados.gov.br/).

Para acessar os dado diretamente da fonte, [clique aqui](http://www.dados.gov.br/dataset/bolsa-familia-saques/resource/2766c225-4415-4e25-a48a-de59db0f3c82).

O arquivo obtido inicialmente é um `.zip` chamado `201910_BolsaFamilia_Saques.zip` com o tamanho de `192M`.

Após realizar a descompactação, você terá o arquivo `201910_BolsaFamilia_Saques.csv` com 12.985.125 linhas com o tamanho de `1,4G`.


## Dicionário de dados

Cada linha desse arquivo `.csv` possui as seguintes informações:

| Coluna                 | Descrição                                                                                                       |
|------------------------|-----------------------------------------------------------------------------------------------------------------|
| Ano/Mês Referência     | Ano/Mês da folha de pagamento                                                                                   |
| Ano/Mês Referência     | Ano/Mês a que se refere a parcela                                                                               |
| UF                     | Sigla da Unidade Federativa do beneficiário do Bolsa Família                                                    |
| Código SIAFI Município | Código, no SIAFI (Sistema Integrado de Administração Financeira), do município do beneficiário do Bolsa Família |
| Nome Município         | Nome do município do beneficiário do Bolsa Família                                                              |
| NIS Beneficiário*      | NIS do beneficiário do Bolsa Família                                                                            |
| Nome Beneficiário      | Nome do beneficiário do Bolsa Família                                                                           |
| Data Saque             | Data em que foi realizado o saque                                                                               |
| Valor Saque            | Valor da parcela do benefício                                                                                   | 

\*: Criado pela Caixa Econômica Federal o NIS significa Número de Identificação Social e é 
ganho quando o cidadão brasileiro ingressa em algum Programa Social, seja o Bolsa Família, 
FGTS, emitiu sua Carteira de Trabalho, tornou-se contribuinte do INSS ou iniciou sua vida como 
trabalhador de iniciativa privada ou pública.

Para acessar o dicionário de dados diretamente, [clique aqui](http://www.portaltransparencia.gov.br/pagina-interna/603401-dicionario-de-dados-bolsa-familia-saques).

## Processamento dos dados

### 1. Separação em 15 arquivos a serem processados

Como o arquivo de `.csv` que é obtido ao extrair o `zip` é muito grande (1.4G) e o GitHub não permite uploads de arquivos
maiores que 100MB, foi realizado a separação desse `.csv` em 15 arquivos `.csv`.

Esse tipo de separação também ajudará na hora de consumir os dados, pois
não será necessário abrir um único arquivo grande, muitas vezes onerando a máquina.

O comando abaixo gera 15 arquivos `.csv` com base no `201910_BolsaFamilia_Saques.csv`, cada um com 900.000 linhas e com o prefixo `saque_`.

```
split -d -l 900000 --additional-suffix=.csv 201910_BolsaFamilia_Saques.csv saque_
```

Ao final da execução do comando acima, é esperado que o diretório tenha o seguinte conteúdo:

```
-rw-rw-r-- 1 vitor vitor  93M fev 24 23:03 saque_00.csv
-rw-rw-r-- 1 vitor vitor  92M fev 24 23:03 saque_01.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_02.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_03.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_04.csv
-rw-rw-r-- 1 vitor vitor  95M fev 24 23:03 saque_05.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_06.csv
-rw-rw-r-- 1 vitor vitor  93M fev 24 23:03 saque_07.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_08.csv
-rw-rw-r-- 1 vitor vitor  95M fev 24 23:03 saque_09.csv
-rw-rw-r-- 1 vitor vitor  94M fev 24 23:03 saque_10.csv
-rw-rw-r-- 1 vitor vitor  95M fev 24 23:03 saque_11.csv
-rw-rw-r-- 1 vitor vitor  93M fev 24 23:03 saque_12.csv
-rw-rw-r-- 1 vitor vitor  93M fev 24 23:03 saque_13.csv
-rw-rw-r-- 1 vitor vitor  40M fev 24 23:03 saque_14.csv
```

Esses arquivos podem ser encontrados na pasta `dataset`. O arquivo bruto inicial deve ser baixo diretamente
pelo Portal, caso tenha interesse em obtê-lo execute o comando abaixo:

```
wget http://www.portaltransparencia.gov.br/download-de-dados/bolsa-familia-saques/201910
```

### 2. Conversão de csv para json

Para converter os arquivos de csv para json é necessário executar o script
`convert_csv_to_json`.

Ele irá percorrer cada arquivo csv e gerará um json correspondente.

O arquivo JSON será um array de documentos conforme abaixo:
```
{
  "pessoa": {
    "nis": "",
    "nome_completo": {
      "nome": "Nome",
      "sobrenome": "Sobrenome de Oliveira"
    }
  },
  "data_saque": "18-10-2019",
  "saque": 171,
  "municipio": {
    "localizacao": {
      "lat": -10.995,
      "lon": -68.7497
    },
    "nome": "Brasileia",
    "siafi": "0105",
    "uf": "AC"
  }
}
```

Nem todas as linhas dos arquivo `.csv` puderem ser convertidas, sendo assim, ao final do script
é gerado um arquivo `erros_saques.csv` com as linhas que não puderem
ser transformadas para JSON. Isso ocorre, pois na geração do documento JSON, é adicionado
a latitude e longitude do documento e nem sempre o município pode ser encontrado.

### 3. Inserção no ElasticSearch

Para inserir os dados é necessário a execução do script `send_bulk_es.py`. Ele irá utilizar
os arquivos JSON gerados e irá enviar de 500 em 500 documentos.

Ele utiliza [Bulk helpers](https://elasticsearch-py.readthedocs.io/en/master/helpers.html#bulk-helpers)
para agilizar o envio dos dados, visto que se fosse enviado cada documento por request, seria muito
custoso.