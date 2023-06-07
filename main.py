from PIL import Image
from cryptography.fernet import Fernet
import PySimpleGUI as sg
import sys

def getPixels(path):
    img = Image.open(path)
    grid = [[0 for col in range(img.width)] for row in range(img.height)]
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))
            pixel_value = (r << 16) + (g << 8) + b
            grid[y][x] = f"{pixel_value:024b}"
    return grid


def stringToBin(message):
    bin = message.encode()
    encodedMessage = list()
    for byte in bin:
        encodedMessage.append('0' + format(byte, 'b'))
        if len(encodedMessage[-1]) == 7:
            encodedMessage[-1] = '0' + encodedMessage[-1]
    return encodedMessage


def getRatio(grid, message):
    height, width = len(grid), len(grid[0])
    ratio = ((height-2)*width)//((len(message)*4)+4)
    return ratio


def hideRatio(grid, ratio):
    binRatio = format(ratio, 'b')
    if len(binRatio) % 2 == 1:
        binRatio = '0' + binRatio
    pixelsToSet = len(binRatio)//2
    for i in range(pixelsToSet):
        newPixel = str(grid[0][i])
        newPixel = newPixel[:-3] + '1' + binRatio[i*2:(i*2)+2]
        grid[0][i] = newPixel
    lastPixel = grid[0][pixelsToSet-1]
    grid[0][pixelsToSet-1] = lastPixel[:-3] + '0' + lastPixel[-2:]


def hideMessage(grid, ratio, message):
    gridRow, gridColumn = 2, 0
    for i in range(len(message)):
        for j in range(4):
            segment = message[i]
            segment = segment[j*2:(j*2)+2]
            newPixel = str(grid[gridRow][gridColumn])
            newPixel = newPixel[:-2] + segment
            grid[gridRow][gridColumn] = newPixel
            gridColumn += ratio
            while gridColumn >= len(grid[0]):
                gridColumn -= len(grid[0])
                gridRow += 1
    flagSegment = str(grid[gridRow][gridColumn])
    grid[gridRow][gridColumn] = flagSegment[:-2] + '1' + flagSegment[-1]


def newImage(grid):
    height, width = len(grid), len(grid[0])
    img = Image.new('RGB', (width, height))
    binaryList = list()
    for i in range(height):
        for j in range(width):
            pixel = str(grid[i][j])
            binaryList.append(int(pixel[:8], 2))
            binaryList.append(int(pixel[8:16], 2))
            binaryList.append(int(pixel[16:], 2))
    img.putdata([(r, g, b) for r, g, b in zip(binaryList[0::3], binaryList[1::3], binaryList[2::3])])
    layout = [[sg.Text("Inserisci il path della cartella dove salvare l'immagine.")], [sg.Input(), sg.FolderBrowse("Scegli path"), sg.Button("Invia")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    if event == sg.WIN_CLOSED:
        exit()
    path = values["Scegli path"]
    layout = [[sg.Text("Come vuoi chiamare la nuova immagine?")], [sg.Input("immagine_modificata"), sg.Button("Invia")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    if event == sg.WIN_CLOSED:
        exit()
    path += "/" + values[0] + ".png"
    img.save(path)
    layout = [[sg.Text("Vuoi visualizzare l'immagine modificata?")], [sg.Button("Sì"), sg.Button("No")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    if event == 'Sì':
        img.show()


def extractRatio(grid):
    ratio = ''
    for i in range(len(grid[0])):
        pixel = str(grid[0][i])
        ratio += pixel[-2:]
        if pixel[-3] == '0':
            break
    return int(ratio, 2)


def getMessage(grid, ratio):
    gridRow, gridColumn = 2, 0
    message = list()
    while True:
        segment = ''
        for i in range(4):
            pixel = str(grid[gridRow][gridColumn])
            segment += pixel[-2:]
            gridColumn += ratio
            while gridColumn >= len(grid[0]):
                gridColumn -= len(grid[0])
                gridRow += 1
        if segment[0] == '1':
            break
        message.append(segment)
    return message


def binToString(message):
    output = ''
    for i in range(len(message)):
        binaryStr = message[i]
        output += chr(int(binaryStr, 2))
    return output


def cryptMessage(message):
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encMessage = fernet.encrypt(message.encode())
    return str(encMessage), key


def hideKey(grid, key):
    encodedKey = list()
    compactEncodedKey = ''
    for byte in key:
        encodedKey.append('0' + format(byte, 'b'))
        if len(encodedKey[-1]) == 7:
            encodedKey[-1] = '0' + encodedKey[-1]
    for el in encodedKey:
        compactEncodedKey += el
    pixelsToSet = len(compactEncodedKey)//2
    for i in range(pixelsToSet):
        newPixel = str(grid[1][i])
        newPixel = newPixel[:-3] + '1' + compactEncodedKey[i*2:(i*2)+2]
        grid[1][i] = newPixel
    lastPixel = grid[1][pixelsToSet-1]
    grid[1][pixelsToSet-1] = lastPixel[:-3] + '0' + lastPixel[-2:]


def extractKey(grid):
    key = list()
    character = ''
    for i in range(len(grid[1])):
        pixel = str(grid[1][i])
        character += pixel[-2:]
        if pixel[-3] == '0':
            break
        if len(character) == 8:
            key.append(character)
            character = ''
    return key


def exit():
    layout = [[sg.Text("Grazie per aver usato l'applicazione, arrivederci.")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    sys.exit(0)


def saveMessage(decMessage):
    layout = [[sg.Text("Inserisci il path della cartella dove salvare il testo.")], [sg.Input(), sg.FolderBrowse("Scegli path"), sg.Button("Invia")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    if event == sg.WIN_CLOSED:
        exit()
    path = values["Scegli path"]
    layout = [[sg.Text("Come vuoi chiamare il file di testo?")], [sg.Input("messaggio_nascosto"), sg.Button("Invia")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()
    if event == sg.WIN_CLOSED:
        exit()
    path += "/" + values[0] + ".txt"
    with open(path, "w") as file:
        file.write(decMessage)
    layout = [[sg.Text("File salvato correttamente.")], [sg.Button("Chiudi")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event, values = window.read()
    window.close()


def main():
    layout = [[sg.Text("Cosa vuoi fare?")], [sg.Button("Nascondi un messaggio")], [sg.Button("Estrai un messaggio")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event1, values = window.read()
    window.close()
    if event1 == sg.WIN_CLOSED:
        exit()
    layout = [[sg.Text("Inserisci il path dell'immagine.")], [sg.Input(), sg.FileBrowse("Seleziona file"), sg.Button("Invia")]]
    window = sg.Window("Steganografia", layout, margins=(100, 50))
    event2, values = window.read()
    window.close()
    if event2 == sg.WIN_CLOSED:
        exit()
    grid = getPixels(values["Seleziona file"])
    if event1 == "Nascondi un messaggio":
        layout = [[sg.Text("Vuoi nascondere il testo di un file?")], [sg.Button("Sì"), sg.Button("No")]]
        window = sg.Window("Steganografia", layout, margins=(100, 50))
        event, values = window.read()
        window.close()
        if event == sg.WIN_CLOSED:
            exit()
        elif event == "Sì":
            layout = [[sg.Text("Seleziona il file da cui prelevare il testo.")], [sg.Input(), sg.FileBrowse("Seleziona file"), sg.Button("Invia")]]
            window = sg.Window("Steganografia", layout, margins=(100, 50))
            event, values = window.read()
            window.close()
            if event == sg.WIN_CLOSED:
                exit()
            with open(values["Seleziona file"], "r") as file:
                message, key = cryptMessage(file.read())
        else:
            layout = [[sg.Text("Inserisci il messaggio da nascondere.")], [sg.Multiline(size=(30, 5), key="textbox"), sg.Button("Invia")]]
            window = sg.Window("Steganografia", layout, margins=(100, 50))
            event, values = window.read()
            window.close()
            if event == sg.WIN_CLOSED:
                exit()
            message, key = cryptMessage(values["textbox"])
        message = stringToBin(message)
        ratio = getRatio(grid, message)
        if ratio >= 1:
            hideRatio(grid, ratio)
            hideKey(grid, key)
            hideMessage(grid, ratio, message)
            newImage(grid)
        else:
            layout = [[sg.Text("ERRORE: il messaggio è troppo grande per poter essere inserito nell'immagine.")], [sg.Button("Chiudi")]]
            window = sg.Window("Steganografia", layout, margins=(100, 50))
            event, values = window.read()
            window.close()
    elif event1 == "Estrai un messaggio":
        ratio = extractRatio(grid)
        key = binToString(extractKey(grid)) + '='
        encKey = key.encode()
        fernet = Fernet(encKey)
        encMessage = binToString(getMessage(grid, ratio))
        encMessage = encMessage[2:-1].encode()
        decMessage = fernet.decrypt(encMessage).decode()
        column = [[sg.Text("Il messaggio nascosto nell'immagine è il seguente:")], [sg.Text(decMessage)], [sg.Button("Chiudi"), sg.Button("Salva")]]
        layout = [[sg.Column(column, scrollable = True, size=(500, 200))]]
        window = sg.Window("Steganografia", layout, resizable=True)
        event, values = window.read()
        window.close()
        if event == "Salva":
            saveMessage(decMessage)
    exit()


if __name__ == "__main__":
    main()