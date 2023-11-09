import string
import easyocr

# Inicializar o leitor OCR
leitor = easyocr.Reader(['en'], gpu=False)

# Mapeando dicionários para conversão de caracteres
dict_char_to_int = {'O': '0',
                    'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5'}

dict_int_to_char = {'0': 'O',
                    '1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    '5': 'S'}


def gravar_csv(resultados, path_saida):
    """
    Gravar os resultados em um arquivo CSV

    Args:
        resultados (dict): Dicionário contendo os resultados.
        path_saida (str): Caminho de para salvar o arquivo de saída.
    """
    with open(path_saida, 'w') as f:
        f.write('{},{},{},{},{},{},{}\n'.format('frame_nmr', 'carro_id', 'carro_bbox',
                                                'placa_carro_bbox', 'placa_carro_bbox_acuracia', 'numero_placa',
                                                'numero_placa_acuracia'))

        for frame_nmr in resultados.keys():
            for carro_id in resultados[frame_nmr].keys():
                print(resultados[frame_nmr][carro_id])
                if 'carro' in resultados[frame_nmr][carro_id].keys() and \
                   'placa_carro' in resultados[frame_nmr][carro_id].keys() and \
                   'texto' in resultados[frame_nmr][carro_id]['placa_carro'].keys():
                    f.write('{},{},{},{},{},{},{}\n'.format(frame_nmr,
                                                            carro_id,
                                                            '[{} {} {} {}]'.format(
                                                                resultados[frame_nmr][carro_id]['carro']['bbox'][0],
                                                                resultados[frame_nmr][carro_id]['carro']['bbox'][1],
                                                                resultados[frame_nmr][carro_id]['carro']['bbox'][2],
                                                                resultados[frame_nmr][carro_id]['carro']['bbox'][3]),
                                                            '[{} {} {} {}]'.format(
                                                                resultados[frame_nmr][carro_id]['placa_carro']['bbox'][0],
                                                                resultados[frame_nmr][carro_id]['placa_carro']['bbox'][1],
                                                                resultados[frame_nmr][carro_id]['placa_carro']['bbox'][2],
                                                                resultados[frame_nmr][carro_id]['placa_carro']['bbox'][3]),
                                                            resultados[frame_nmr][carro_id]['placa_carro']['bbox_acuracia'],
                                                            resultados[frame_nmr][carro_id]['placa_carro']['texto'],
                                                            resultados[frame_nmr][carro_id]['placa_carro']['texto_acuracia'])
                            )
        f.close()


def compilar_placa_carro(texto):
    """
    Verifique se o texto da placa está de acordo com o formato exigido.

    Args:
        texto (str): Texto da placa do carro.

    Returns:
        bool: Se a placa do carro estiver em conforme com o formato retorna True, ao contrário retorna False.
    """
    if len(texto) != 7:
        return False

    if (texto[0] in string.ascii_uppercase or texto[0] in dict_int_to_char.keys()) and \
       (texto[1] in string.ascii_uppercase or texto[1] in dict_int_to_char.keys()) and \
       (texto[2] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or texto[2] in dict_char_to_int.keys()) and \
       (texto[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or texto[3] in dict_char_to_int.keys()) and \
       (texto[4] in string.ascii_uppercase or texto[4] in dict_int_to_char.keys()) and \
       (texto[5] in string.ascii_uppercase or texto[5] in dict_int_to_char.keys()) and \
       (texto[6] in string.ascii_uppercase or texto[6] in dict_int_to_char.keys()):
        return True
    else:
        return False


def formatar_placa_carro(texto):
    """
    Format the license plate text by converting characters using the mapping dictionaries.

    Args:
        texto (str): License plate text.

    Returns:
        str: Formatted license plate text.
    """
    placa_carro_ = ''
    mapeamento = {0: dict_int_to_char, 1: dict_int_to_char, 4: dict_int_to_char, 5: dict_int_to_char, 6: dict_int_to_char,
               2: dict_char_to_int, 3: dict_char_to_int}
    for j in [0, 1, 2, 3, 4, 5, 6]:
        if texto[j] in mapeamento[j].keys():
            placa_carro_ += mapeamento[j][texto[j]]
        else:
            placa_carro_ += texto[j]

    return placa_carro_


def ler_placa_carro(placa_carro_cortada):
    """
    Ler o texto da placa da imagem recortada fornecida.

    Args:
        placa_carro_cortada (PIL.Image.Image): Imagem recortada contendo a placa do carro.

    Returns:
        tuple: Tupla contendo o texto formatado da placa e sua acuracia.
    """

    deteccoes = leitor.readtext(placa_carro_cortada)

    for deteccao in deteccoes:
        bbox, texto, acuracia = deteccao

        texto = texto.upper().replace(' ', '')

        if compilar_placa_carro(texto):
            return formatar_placa_carro(texto), acuracia

    return None, None


def get_carro(placa_carro, veiculo_acp_ids):
    """
    Recupere as coordenadas e a identificação do veículo com base nas coordenadas da placa.

    Args:
        placa_carro (tuple): Tupla contendo as coordenadas da placa (x1, y1, x2, y2, acuracia, classe_id).
        veiculo_acp_ids (list): Lista de IDs de rastreamento de veículos e suas correspondentes coordenadas

    Returns:
        tuple: Lista de IDs de rastreamento de veículos e suas correspondentes coordenadas.(x1, y1, x2, y2)
    """
    x1, y1, x2, y2, acuracia, classe_id = placa_carro

    foundIt = False
    for j in range(len(veiculo_acp_ids)):
        xcar1, ycar1, xcar2, ycar2, carro_id = veiculo_acp_ids[j]
    #
        if x1 > xcar1 and y1 > ycar1 and x2 < xcar2 and y2 < ycar2:
            carro_indx = j
            foundIt = True
            break
    #
    if foundIt:
        return veiculo_acp_ids[carro_indx]

    return -1, -1, -1, -1, -1
