usuarios = [] 

while True:
    print("\nMenu Principal")
    opcion = input('1.- Crear nuevo usuario\n2.- Consultar informacion\n3.- Salir\nElige una opción: ')
    
    if opcion == '1':
        nombre = input('Ingresa el nombre: ')
        sueldo = input('Ingresa el sueldo: ')
        posicion = input('Ingresa la posición: ')
        
        usuarios.append([nombre, sueldo, posicion])
        print("Usuario guardado")
        
    elif opcion == '2':
        nombre_buscar = input('Ingresa tu nombre: ')
        
        for persona in usuarios:
            if persona[0].lower() == nombre_buscar.lower():
                print(f"\n--- Datos de {persona[0]} ---")
                print(f"Sueldo: ${persona[1]}")
                print(f"Posición: {persona[2]}")
                encontrado = True
                break 
        
            
    elif opcion == '3':
        print("Programa terminado")
        break 
        
    else:
        print("Opción no válida")
        
