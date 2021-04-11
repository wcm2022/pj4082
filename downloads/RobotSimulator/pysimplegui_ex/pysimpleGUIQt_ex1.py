import PySimpleGUIQt as sg

layout = [[sg.Text('開始採用 PySimpleGUI!'),sg.Text(' '*5), sg.Text('On the same row'), ],
          [sg.Text('Input something here'), sg.Input('default text')],
          [sg.Text('Another line of text')]]

window = sg.Window('My first QT Window').Layout(layout)

event, values = window.Read()