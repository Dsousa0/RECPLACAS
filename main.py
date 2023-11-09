from ultralytics import YOLO
import cv2
import tkinter as tk
from tkinter import ttk
from sort.sort import *
from util import get_carro, ler_placa_carro, gravar_csv
import threading
import PIL.Image
import PIL.ImageTk

captura_ativa = False
captura_camera = None
resultados = {}
frame_nmr = -1


def iniciar_captura():
    global captura_ativa, captura_camera, resultados, frame_nmr
    captura_ativa = True
    botao_iniciar.config(state='disabled')
    botao_parar.config(state='normal')

    frame_nmr = -1
    resultados = {}

    captura_camera = cv2.VideoCapture(0)


    thread = threading.Thread(target=capturar_video)
    thread.start()


def parar_captura():
    global captura_ativa
    captura_ativa = False
    botao_iniciar.config(state='normal')
    botao_parar.config(state='disabled')


def capturar_video():
    global resultados, frame_nmr

    while captura_ativa:
        frame_nmr += 1
        ret, frame = captura_camera.read()
        if not ret:
            break

        resultados[frame_nmr] = {}

        # Detect vehicles, track them, and detect car plates
        deteccoes = modelo_coco(frame)[0]
        deteccoes_ = []

        for detecao in deteccoes.boxes.data.tolist():
            x1, y1, x2, y2, acuracia, classe_id = detecao
            if int(classe_id) in veiculos:
                deteccoes_.append([x1, y1, x2, y2, acuracia])

        rastreio_veiculos = mot_tracker.update(np.asarray(deteccoes_))

        placas_carros = modelo_placa_carro(frame)[0]

        for placa in placas_carros.boxes.data.tolist():
            x1, y1, x2, y2, acuracia, classe_id = placa

            xcar1, ycar1, xcar2, ycar2, carro_id = get_carro(placa, rastreio_veiculos)

            if carro_id != -1:
                placa_cortada = frame[int(y1):int(y2), int(x1):int(x2), :]
                placa_carro_cinza = cv2.cvtColor(placa_cortada, cv2.COLOR_BGR2GRAY)
                _, placa_carro_cinza_thresh = cv2.threshold(placa_carro_cinza, 64, 255, cv2.THRESH_BINARY_INV)
                texto_placa_carro, acuracia_texto_placa_carro = ler_placa_carro(placa_carro_cinza_thresh)

                if texto_placa_carro is not None:
                    resultados[frame_nmr][carro_id] = {'carro': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                                                       'placa_carro': {'bbox': [x1, y1, x2, y2],
                                                                       'texto': texto_placa_carro,
                                                                       'bbox_acuracia': acuracia,
                                                                       'texto_acuracia': acuracia_texto_placa_carro}}

        # Atualize o Canvas com o quadro de vídeo
        atualizar_canvas(frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or not captura_ativa:
            break

    if captura_ativa:
        gravar_csv(resultados, './testCAMHD12.csv')

    captura_camera.release()
    cv2.destroyAllWindows()


def atualizar_canvas(frame):
    # Converta o quadro OpenCV em um objeto de imagem Pillow
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = PIL.Image.fromarray(frame)

    # Crie uma representação de imagem para exibir no Canvas
    photo = PIL.ImageTk.PhotoImage(image=frame)

    # Atualize a imagem no Canvas
    canvas.create_image(canvas.winfo_width() / 2, canvas.winfo_height() / 2, image=photo)
    canvas.image = photo  # Mantenha uma referência


# Inicialize a interface gráfica
root = tk.Tk()
root.title('REC-PLACAS')

window_width = 1000
window_height = 600

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

center_x = int(screen_width / 2 - window_width / 2)
center_y = int(screen_height / 2 - window_height / 2)

root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
root.resizable(False, False)

frame = tk.Frame(root, border=1, relief=tk.RAISED)
frame.pack(side=tk.BOTTOM, fill=tk.X)

style = ttk.Style()
style.configure('Green.TButton', background='green', font=('', 10, 'bold'))
botao_iniciar = ttk.Button(frame, text='Iniciar Captura', style='Green.TButton', command=iniciar_captura)
botao_iniciar.pack(ipadx=10, ipady=10, padx=20, pady=20, fill=tk.X, expand=True, anchor=tk.SW, side=tk.LEFT)

style.configure('Red.TButton', background='red', font=('', 10, 'bold'))
botao_parar = ttk.Button(frame, text='Parar Captura', style='Red.TButton', command=parar_captura)
botao_parar.config(state='disabled')
botao_parar.pack(ipadx=10, ipady=10, padx=20, pady=20, fill=tk.X, expand=True, anchor=tk.SE, side=tk.RIGHT)

# Crie um Canvas para exibir o vídeo
canvas = tk.Canvas(root, width=1000, height=600)
canvas.pack(padx=20, pady=20)

mot_tracker = Sort()
modelo_coco = YOLO('yolov8n.pt')
modelo_placa_carro = YOLO('models/RecPlacas.pt')

veiculos = [2, 3, 5, 7]

# Inicialize a interface gráfica
root.mainloop()
