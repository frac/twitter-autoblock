#!/usr/bin/python
#
#   Author : Pierre-Jean Coudert
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 of the License.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
 
import Tkinter as tk   

class Balloon(tk.Toplevel): 
    """
    root = tk.Tk()  
    lab1=tk.Label(root,text='Balloon 1')  
    lab1.pack()  
    i1 = Balloon(parent=lab1,texte="Balloon 1")  
    root.mainloop()
    """
    
    def __init__(self, parent=None, aText='', aDelay=400): 
        tk.Toplevel.__init__(self,parent,bd=1,bg='black')  
        self._duration = aDelay 
        self._mousePoint = None
        self.parent = parent        
        self.withdraw()  
        self.overrideredirect(1)  
        self.transient() 
        self._label = tk.Label(self, text=aText, bg="#FFFFE0",justify='left')  
        self._label.update_idletasks()  
        self._label.pack()  
        self.settext(aText)
        self.parent.bind('<Enter>',self._delay)  
        self.parent.bind('<Button-1>',self._hide)  
        self.parent.bind('<Leave>',self._hide)  
        
    def settext(self, aText=''): 
        self._label["text"]=aText
        self._label.update_idletasks()  
        self._tipwidth = self._label.winfo_width()  
        self._tipheight = self._label.winfo_height()  
        
    def gettext(self): 
        return self._label["text"]
        
    def disable(self): 
        self.parent.bind('<Enter>',self._disable)  
        
    def enable(self): 
        self.parent.bind('<Enter>',self._delay)  

    def _delay(self, event): 
        self._mousePoint = (event.x_root, event.y_root)
        self.action=self.parent.after(self._duration,self._display)
          
    def _display(self): 
        self.update_idletasks()  
        if not self._mousePoint :
            return           
        posX = min(self._mousePoint[0], self.winfo_screenwidth()-self._tipwidth)
        posY = max(0,self.parent.winfo_rooty()-self._tipheight)
        self.geometry('+%d+%d'%(posX,posY))  
        self.deiconify()  
        self.lift()        
        
    def _hide(self,event): 
        self.withdraw()  
        self.parent.after_cancel(self.action) 
          
    def _disable(self,event): 
        self.withdraw()  
        self.action=self.parent.after(self._duration,self._nothing)

    def _nothing(self): 
        pass
    