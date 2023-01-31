from tkinter import Tk, Label, Button, Text, messagebox
import socket

PATH = "Z:/Обмен/Никите Романовичу/ip.txt"

window = Tk()
window.title("IP test")
window.geometry("300x120+810+460")

ipLabel = Label(window, text=socket.gethostbyname(socket.gethostname()), font=("Arial", 24))
ipLabel.pack(expand=True)

inputtxt = Text(window, height=1, width=20)
inputtxt.pack(expand=True)

def buttonClick():
    input = inputtxt.get(1.0, "end-1c")
    if not input:
        messagebox.showerror(message="Введите имя")
        return
    try:
        with open(PATH, 'r+') as f:
            f.seek(0, 2)
            f.write(f'{socket.gethostbyname(socket.gethostname())}: {input} \n')
            messagebox.showinfo(title=None, message=f"{input} успешно записан")
    except Exception as err:
        messagebox.showerror(message=str(err))

writeButton = Button(window, text="Записать", command=buttonClick)
writeButton.pack(expand=True)

window.mainloop()


