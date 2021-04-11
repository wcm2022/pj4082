# -*- coding: utf-8 -*-
# https://www.jianshu.com/u/69f40328d4f0
# https://github.com/china-testing/python-api-tesing
# https://china-testing.github.io/
# support q group: 630011153 144081101
import PySimpleGUI as sg
 
# Create some widgets
ok_btn = sg.Button('Open Second Window')
cancel_btn = sg.Button('Cancel')
layout = [[ok_btn, cancel_btn]]
 
# Create the first Window
window = sg.Window('Window 1', layout)
 
win2_active = False
 
# Create the event loop
while True:
    event1, values1 = window.read(timeout=100)
 
    if event1 in (None, 'Cancel'):
        # User closed the Window or hit the Cancel button
        break
 
    if not win2_active and event1 == 'Open Second Window':
        win2_active = True
        layout2 = [[sg.Text('Window 2')],
                   [sg.Button('Exit')]]
 
        window2 = sg.Window('Window 2', layout2)
 
    if win2_active:
        events2, values2 = window2.Read(timeout=100)
        if events2 is None or events2 == 'Exit':
            win2_active  = False
            window2.close()
 
window.close()