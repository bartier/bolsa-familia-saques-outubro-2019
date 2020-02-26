import os
import csv
import json
import unidecode
import sys


def replace_prepositions(s):
    s = s.replace(" Da ", " da ")
    s = s.replace(" De ", " de ")
    s = s.replace(" Do ", " do ")
    s = s.replace(" Dos ", " dos ")
    s = s.replace(" Das ", " das ")
    return s


class DataSetHandler:

    def __init__(self, files_prefix, directory, google_api_key=None):
        self.files_prefix = files_prefix
        self.directory = directory

        with open(f'{directory}/estados.json', encoding="utf-8-sig") as estados_json:
            self.estados = json.load(estados_json)

        with open(f'{directory}/municipios.json', encoding="utf-8-sig") as municipios_json:
            self.municipios = json.load(municipios_json)

        self.tmp_municipio = {
            "nome": "",
            "codigo_uf": ""
        }

        self.GOOGLE_API_KEY = google_api_key
        self.erros = []

    def find_files_to_process(self):
        files_to_process = []

        index = 0
        while True:

            # if index in [0, 1, 2]:
            #     index += 1
            #     continue

            filename = f'{self.directory}/{self.files_prefix}_{str(index).zfill(2)}.csv'

            if os.path.exists(filename):
                files_to_process.append(filename)
                index += 1
            else:
                return files_to_process

    def is_first_file(self, file):
        if file == f'{self.directory}/{self.files_prefix}_00.csv':
            return True
        return False

    def save_saques_in_json_file(self, from_file, saques):
        try:
            index = os.path.splitext(from_file.split("_")[1])[0]
        except Exception:
            print("Não foi possível gerar o index do arquivo json com base no arquivo .csv lido", file=sys.stderr)
            print("Utilizando index negativo.", file=sys.stderr)
            index = -1

        filename_to_save = f'{self.directory}/{self.files_prefix}_{index}.json'

        with open(filename_to_save, 'w') as fp:
            json.dump(saques, fp)

        print(f'Salvado arquivo {filename_to_save}')

    def process_dataset(self):
        files = self.find_files_to_process()

        for file in files:

            print(f'Processing {file}...')

            with open(file, encoding='ISO-8859-1') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=";")

                saques_bolsa_familia = []

                line_count = 0
                for row in csv_reader:

                    if line_count % 100 == 0:
                        print(f'Processing item {line_count + 1} from {file}')

                    if self.is_first_file(file) and line_count == 0:
                        pass
                    else:
                        try:
                            saque = self.get_saque_bolsa_familia(row, line_count)
                        except Exception:
                            self.erros.append(row)
                        saques_bolsa_familia.append(saque)
                    line_count += 1

                self.save_saques_in_json_file(file, saques_bolsa_familia)

        with open('erros_saques.csv', "w") as csv_erros:
            csv_writer = csv.writer(csv_erros)
            csv_writer.writerows(self.erros)

    def get_saque_bolsa_familia(self, row, index):

        saque = self.get_saque(row)
        data_saque = self.get_data_saque(row)
        nomes = self.get_nomes(row)

        pessoa_primeiro_nome = nomes[0]
        pessoa_sobrenome = self.get_pessoa_sobrenome(nomes)

        pessoa_nis = row[5]

        municipio_nome = self.get_municipio_nome(row)
        municipio_siafi = row[3]

        uf = row[2]

        # competencia_ano = row[1][0:4]
        # competencia_mes = row[1][4:]
        #
        # referencia_ano = row[0][0:4]
        # referencia_mes = row[0][4:]

        municipio_lat, municipio_lon = self.get_municipio_lat_lon(municipio_nome, uf, index)

        return {
            "pessoa": {
                "nis": pessoa_nis,
                "nome_completo": {
                    "nome": pessoa_primeiro_nome,
                    "sobrenome": pessoa_sobrenome
                }
            },
            "data_saque": data_saque,
            "saque": saque,
            "municipio": {
                "localizacao": {
                    "lat": municipio_lat,
                    "lon": municipio_lon,
                },
                "nome": municipio_nome,
                "siafi": municipio_siafi,
                "uf": uf
            }
        }

    def get_municipio_nome(self, row):
        municipio_nome = row[4].title()
        municipio_nome = replace_prepositions(municipio_nome)
        return municipio_nome

    def get_pessoa_sobrenome(self, nomes):
        pessoa_sobrenome = ""
        for i in range(len(nomes)):
            if i != 0:
                pessoa_sobrenome += nomes[i] + " "
        pessoa_sobrenome = pessoa_sobrenome.strip()
        return pessoa_sobrenome

    def get_nomes(self, row):
        nome_beneficiario = row[6].title()
        nome_beneficiario = replace_prepositions(nome_beneficiario)
        nomes = nome_beneficiario.split(" ")
        return nomes

    def get_data_saque(self, row):
        data_saque = row[7]
        data_saque = data_saque.replace('/', "-")
        return data_saque

    def get_saque(self, row):
        saque = row[8]
        saque = saque.replace(",", ".")
        saque = float(saque)
        return saque

    def get_municipio_lat_lon(self, municipio_nome, uf, index):
        uf_codigo = [estado["codigo_uf"] for estado in self.estados if estado["uf"] == uf][0]

        if unidecode.unidecode(replace_prepositions(self.tmp_municipio["nome"])).lower() == municipio_nome.lower() and \
                self.tmp_municipio["codigo_uf"] == uf_codigo:
            return self.tmp_municipio["latitude"], self.tmp_municipio["longitude"]

        municipio_obtido = None
        print(f'{index}. Alterou a cidade para {municipio_nome}')
        municipio_obtido = [municipio for municipio in self.municipios
                            if unidecode.unidecode(
                replace_prepositions(municipio["nome"])).lower() == municipio_nome.lower() and
                            municipio["codigo_uf"] == uf_codigo][0]

        self.tmp_municipio = municipio_obtido

        return municipio_obtido["latitude"], municipio_obtido["longitude"]
