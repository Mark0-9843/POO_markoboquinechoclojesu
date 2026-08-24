"""choclotest.py
   Codigo que permite ingresar datos y que we impriman en la consola
   Autor: Cesar David/Choclititito"""

def main(): #Funcion para el ingreso de datos
    Nombre = input("Ingresa tu nombre: ")  
    Peso = input("Ingresa tu peso: ")  
    EstadoCivil= input("Ingresa tu estado civil: ")  
    Edad = input("Ingresa tu edad: ")  
    DomicilioFiscal = input("Ingresa tu domicilio fiscal: ")  
    Estadoderesidencia = input("Ingresa tu estado de residencia: ")  

    print(f"Tus datos son:  {Nombre}, {Peso}, {EstadoCivil}, {Edad}, {DomicilioFiscal}, {Estadoderesidencia}") # Impresion de los datos en la consola

if __name__ == "__main__": #Iniciacion del codigo
    main()