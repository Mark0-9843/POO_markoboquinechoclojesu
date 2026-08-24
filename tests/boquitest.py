def registrar_usuarios():
    # Creamos una lista vacía para guardar los datos
    lista_usuarios = []

    print("Bienvenido al sistema de registro.")
    
    while True:
        print("\n--- Nuevo Registro ---")
        # Pedimos los datos al usuario
        nombre = input("Ingresa los numeros de tu tarjeta : ")
        
        # Si el usuario escribe 'salir', rompemos el ciclo
        if nombre.lower() == 'salir':
            break
            
        edad = input("Ingresa la edad: ")
        correo = input("Ingresa el correo electrónico: ")
        
        # Agrupamos los datos de esta persona en un diccionario
        usuario = {
            "Nombre": nombre,
            "Edad": edad,
            "Correo": correo
        }
        
        # Agregamos el diccionario a nuestra lista principal
        lista_usuarios.append(usuario)
        print(f" ¡{nombre} ha sido agregado con éxito!")

    # Al salir del ciclo, mostramos los resultados
    print("\n--- Lista de Usuarios Registrados ---")
    if len(lista_usuarios) == 0:
        print("No se registraron usuarios.")
    else:
        for i, usuario in enumerate(lista_usuarios, 1):
            print(f"{i}. Nombre: {usuario['Nombre']} | Edad: {usuario['Edad']} | Correo: {usuario['Correo']}")

# Ejecutamos la función
registrar_usuarios()