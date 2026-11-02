# Uso de arreglos unidimensionales en la gestión de pedidos e inventario
#
# El inventario y los pedidos se guardan en dos listas unidimensionales donde cada
# posición contiene un registro con campos identificados por nombre, permitiendo
# leer por índice, modificar un elemento y recorrer los registros sin usar matrices.
# Las listas de Python son dinámicas y almacenan referencias, por lo que no supuse
# que todos los valores de sus registros estén juntos físicamente en memoria.
#
# Organicé cada acción en una función para mantener separadas la entrada de datos,
# las reglas del inventario y la presentación, considerando los pedidos como reservas
# que descuentan unidades al crearse y las devuelven al editarse o cancelarse.

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext


# Estas constantes permiten cambiar la moneda de presentación y el límite comercial
# sin modificar las reglas de stock, con fechas completas en la zona del ejemplo.
MONEDA = 'USD'
PRECIO_MAXIMO = Decimal('999999999.99')
ZONA_HORARIA = timezone(timedelta(hours=-5))


# Las validaciones devuelven valores utilizables para no repetir conversiones en
# cada operación, rechazando los datos antes de alterar productos o pedidos.
def validar_texto(valor, nombre):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f'{nombre} no puede estar vacío.')
    return ' '.join(valor.split())


def validar_codigo(codigo):
    return validar_texto(codigo, 'El código').upper()


def validar_cantidad(cantidad, minimo=0):
    if type(cantidad) is not int or cantidad < minimo:
        raise ValueError(f'La cantidad debe ser un entero mayor o igual que {minimo}.')
    return cantidad


def validar_precio(valor):
    if type(valor) not in (str, int, Decimal):
        raise ValueError('El precio debe recibirse como texto, entero o Decimal.')
    try:
        precio = Decimal(valor.replace(',', '.') if isinstance(valor, str) else valor)
    except (InvalidOperation, ValueError):
        raise ValueError('El precio debe ser un número válido.') from None
    if not precio.is_finite() or precio <= 0 or precio > PRECIO_MAXIMO:
        raise ValueError(f'El precio debe ser positivo y no superar {PRECIO_MAXIMO} {MONEDA}.')
    with localcontext() as contexto:
        contexto.prec = 28
        centavos = precio.quantize(Decimal('0.01'))
    if precio != centavos:
        raise ValueError('El precio no puede tener fracciones menores a un centavo.')
    return centavos


def obtener_momento(momento=None):
    momento = datetime.now(ZONA_HORARIA) if momento is None else momento
    if (not isinstance(momento, datetime) or momento.tzinfo is None
            or momento.utcoffset() is None):
        raise ValueError('La fecha debe incluir día, hora y zona horaria.')
    return momento


# La búsqueda devuelve la posición porque la lista se consulta y modifica mediante
# índices que comienzan en cero, usando -1 como señal explícita de registro ausente.
def buscar_producto(inventario, codigo):
    codigo = validar_codigo(codigo)
    for indice in range(len(inventario)):
        if inventario[indice]['codigo'] == codigo:
            return indice
    return -1


def buscar_pedido(pedidos, identificador):
    validar_cantidad(identificador, minimo=1)
    for indice in range(len(pedidos)):
        if pedidos[indice]['id'] == identificador:
            return indice
    return -1


# La lectura mediante la posición localizada evita confundir un código comercial
# o un identificador de pedido con el índice que ocupa actualmente en la lista.
def obtener_producto(inventario, codigo):
    indice = buscar_producto(inventario, codigo)
    if indice == -1:
        raise ValueError('El producto no existe.')
    return inventario[indice]


def obtener_pedido(pedidos, identificador):
    indice = buscar_pedido(pedidos, identificador)
    if indice == -1:
        raise ValueError('El pedido no existe.')
    return pedidos[indice]


# INVENTARIO
#
# El código se mantiene como identidad estable y el nombre no se repite en otro
# producto, mientras el stock representa unidades disponibles y puede empezar en
# cero para registrar un artículo que todavía no tiene existencias.
def registrar_producto(inventario, codigo, nombre, stock, precio):
    codigo = validar_codigo(codigo)
    nombre = validar_texto(nombre, 'El nombre')
    stock = validar_cantidad(stock)
    precio = validar_precio(precio)
    for producto in inventario:
        if producto['codigo'] == codigo:
            raise ValueError('El código ya está registrado. Use editar para actualizarlo.')
        if producto['nombre'].casefold() == nombre.casefold():
            raise ValueError('El producto ya existe con otro código.')
    nuevo = {'codigo': codigo, 'nombre': nombre, 'stock': stock, 'precio': precio}
    inventario.append(nuevo)
    return nuevo


def mostrar_productos(inventario) -> None:
    print('\nLISTADO DE PRODUCTOS')
    if not inventario:
        print('No hay productos registrados.')
        return
    print(f'{"CÓDIGO":<12} {"PRODUCTO":<28} {"DISPONIBLE":>10} {"PRECIO USD":>15}')
    print('-' * 68)
    for producto in inventario:
        print(f'{producto["codigo"]:<12} {producto["nombre"]:<28} '
              f'{producto["stock"]:>10} {producto["precio"]:>15.2f}')


# Antes de escribir los cambios reviso todos los campos para que un precio o nombre
# inválido no deje aplicado sólo el stock, conservando el código para no romper
# la relación con los pedidos y dejando sus precios anteriores sin cambios.
def editar_producto(inventario, codigo, nombre, stock, precio):
    producto = obtener_producto(inventario, codigo)
    nombre = validar_texto(nombre, 'El nombre')
    stock = validar_cantidad(stock)
    precio = validar_precio(precio)
    for otro in inventario:
        if otro is not producto and otro['nombre'].casefold() == nombre.casefold():
            raise ValueError('Otro producto ya utiliza ese nombre.')
    producto.update(nombre=nombre, stock=stock, precio=precio)
    return producto


# Un pedido activo necesita que su producto siga disponible como registro para
# devolver las unidades si se cancela, por eso la eliminación queda bloqueada
# mientras exista esa relación y pop retira únicamente la posición validada.
def eliminar_producto(inventario, pedidos, codigo):
    indice = buscar_producto(inventario, codigo)
    if indice == -1:
        raise ValueError('El producto no existe.')
    codigo = inventario[indice]['codigo']
    for pedido in pedidos:
        if pedido['codigo'] == codigo:
            raise ValueError('El producto tiene pedidos activos. Cancele esos pedidos primero.')
    return inventario.pop(indice)


# PEDIDOS
#
# Cada pedido reserva un solo producto para mantener el alcance del sistema básico
# y guarda el precio acordado al registrarse, de modo que editar el catálogo no
# cambie de manera retroactiva el importe que ya se mostró al cliente.
def registrar_pedido(inventario, pedidos, identificador, cliente, codigo, cantidad, momento=None):
    validar_cantidad(identificador, minimo=1)
    cliente = validar_texto(cliente, 'El cliente')
    cantidad = validar_cantidad(cantidad, minimo=1)
    momento = obtener_momento(momento)
    if buscar_pedido(pedidos, identificador) != -1:
        raise ValueError('El identificador del pedido ya está registrado.')
    producto = obtener_producto(inventario, codigo)
    if cantidad > producto['stock']:
        raise ValueError('No hay unidades suficientes para registrar el pedido.')
    pedido = {'id': identificador, 'cliente': cliente, 'codigo': producto['codigo'],
              'cantidad': cantidad, 'precio_unitario': producto['precio'],
              'creado_en': momento, 'actualizado_en': momento}
    # El descuento se realiza después de todas las validaciones para no reservar
    # unidades por una solicitud que al final no pudo registrarse.
    producto['stock'] -= cantidad
    pedidos.append(pedido)
    return pedido


def calcular_total_pedido(pedido):
    # La precisión crece con la cantidad para multiplicar importes decimales sin
    # perder centavos aunque el número de unidades aumente en futuros registros.
    with localcontext() as contexto:
        contexto.prec = max(28, len(str(pedido['cantidad'])) + 14)
        return pedido['precio_unitario'] * pedido['cantidad']


def mostrar_pedidos(pedidos) -> None:
    print('\nLISTADO DE PEDIDOS')
    if not pedidos:
        print('No hay pedidos registrados.')
        return
    for pedido in pedidos:
        print(f'Pedido {pedido["id"]} | Cliente {pedido["cliente"]} | Producto {pedido["codigo"]}')
        print(f'Cantidad {pedido["cantidad"]} | Precio {pedido["precio_unitario"]:.2f} {MONEDA} | '
              f'Total {calcular_total_pedido(pedido):.2f} {MONEDA}')
        print(f'Creado {pedido["creado_en"].isoformat()} | Actualizado {pedido["actualizado_en"].isoformat()}')
        print('-' * 68)


# Al editar considero las unidades que el mismo pedido ya tenía reservadas para
# que pueda ampliarse sin descontar dos veces su cantidad anterior, comprobando
# primero la disponibilidad del destino si también cambia el producto solicitado.
def editar_pedido(inventario, pedidos, identificador, cliente, codigo, cantidad, momento=None):
    pedido = obtener_pedido(pedidos, identificador)
    cliente = validar_texto(cliente, 'El cliente')
    cantidad = validar_cantidad(cantidad, minimo=1)
    momento = obtener_momento(momento)
    if momento < pedido['creado_en'] or momento < pedido['actualizado_en']:
        raise ValueError('La actualización no puede ser anterior al pedido o a su última edición.')
    anterior = obtener_producto(inventario, pedido['codigo'])
    nuevo = obtener_producto(inventario, codigo)
    mismo_producto = anterior is nuevo
    disponibles = nuevo['stock'] + (pedido['cantidad'] if mismo_producto else 0)
    if cantidad > disponibles:
        raise ValueError('No hay unidades suficientes para aplicar el cambio del pedido.')
    precio = pedido['precio_unitario'] if mismo_producto else nuevo['precio']
    # La devolución y la nueva reserva se aplican juntas después de validar para
    # conservar el stock cuando una edición sea rechazada por falta de unidades.
    anterior['stock'] += pedido['cantidad']
    nuevo['stock'] -= cantidad
    pedido.update(cliente=cliente, codigo=nuevo['codigo'], cantidad=cantidad,
                  precio_unitario=precio, actualizado_en=momento)
    return pedido


def eliminar_pedido(inventario, pedidos, identificador):
    indice = buscar_pedido(pedidos, identificador)
    if indice == -1:
        raise ValueError('El pedido no existe.')
    pedido = pedidos[indice]
    producto = obtener_producto(inventario, pedido['codigo'])
    producto['stock'] += pedido['cantidad']
    return pedidos.pop(indice)


# ENTRADA DE DATOS
#
# Separé estas lecturas de las reglas del sistema para reutilizar las operaciones
# desde otras interfaces sin depender de input, mientras el menú vuelve a preguntar
# ante texto no numérico, cantidades fuera de rango o valores monetarios inválidos.
def leer_texto(mensaje, actual=None):
    while True:
        entrada = input(mensaje)
        if not entrada.strip() and actual is not None:
            return actual
        try:
            return validar_texto(entrada, 'El texto')
        except ValueError as error:
            print(f'Error: {error}')


def leer_entero(mensaje, minimo=0, maximo=None, actual=None):
    while True:
        entrada = input(mensaje).strip()
        if not entrada and actual is not None:
            return actual
        try:
            valor = int(entrada)
        except ValueError:
            print('Error: escriba un número entero, sin letras ni decimales.')
            continue
        try:
            validar_cantidad(valor, minimo)
            if maximo is not None and valor > maximo:
                raise ValueError(f'El valor no puede ser mayor que {maximo}.')
            return valor
        except ValueError as error:
            print(f'Error: {error}')


def leer_precio(mensaje, actual=None):
    while True:
        entrada = input(mensaje).strip()
        if not entrada and actual is not None:
            return actual
        try:
            return validar_precio(entrada)
        except ValueError as error:
            print(f'Error: {error}')


def confirmar(mensaje):
    while True:
        respuesta = input(f'{mensaje} [s/n]: ').strip().casefold()
        if respuesta in ('s', 'si', 'sí'):
            return True
        if respuesta in ('n', 'no'):
            return False
        print('Escriba s para confirmar o n para cancelar.')


# MENÚ DE INVENTARIO
#
# Las opciones llaman a una sola operación principal y muestran el resultado sin
# repetir sus reglas, manteniendo las listas compartidas para que los cambios sean
# visibles al volver al menú de pedidos o al consultar otra vez el inventario.
def menu_inventario(inventario, pedidos) -> None:
    while True:
        print('\nINVENTARIO\n1. Registrar producto\n2. Mostrar productos\n3. Editar producto\n4. Eliminar producto\n0. Volver')
        opcion = leer_entero('Seleccione una opción: ', 0, 4)
        try:
            if opcion == 0:
                return
            if opcion == 1:
                codigo = leer_texto('Código del producto: ')
                nombre = leer_texto('Nombre del producto: ')
                stock = leer_entero('Unidades disponibles: ', 0)
                precio = leer_precio('Precio unitario en USD: ')
                producto = registrar_producto(inventario, codigo, nombre, stock, precio)
                print(f'Producto {producto["codigo"]} registrado correctamente.')
            elif opcion == 2:
                mostrar_productos(inventario)
            elif opcion == 3:
                codigo = leer_texto('Código del producto a editar: ')
                anterior = obtener_producto(inventario, codigo)
                print('Presione Enter para conservar un valor. El stock indicado es el disponible.')
                nombre = leer_texto(f'Nombre [{anterior["nombre"]}]: ', anterior['nombre'])
                stock = leer_entero(f'Stock disponible [{anterior["stock"]}]: ', 0, actual=anterior['stock'])
                precio = leer_precio(f'Precio [{anterior["precio"]:.2f}]: ', anterior['precio'])
                editar_producto(inventario, codigo, nombre, stock, precio)
                print(f'Producto {anterior["codigo"]} actualizado correctamente.')
            elif opcion == 4:
                codigo = leer_texto('Código del producto a eliminar: ')
                producto = obtener_producto(inventario, codigo)
                if confirmar(f'¿Eliminar el producto {producto["codigo"]}?'):
                    eliminado = eliminar_producto(inventario, pedidos, codigo)
                    print(f'Producto {eliminado["codigo"]} eliminado correctamente.')
                else:
                    print('Eliminación cancelada.')
        except ValueError as error:
            print(f'Error: {error}')


# MENÚ DE PEDIDOS
#
# El siguiente identificador aumenta únicamente después de un registro válido y
# no se reduce al borrar pedidos para evitar reutilizar un número durante la sesión,
# devolviéndolo al menú principal cuando el usuario decide volver al inventario.
def menu_pedidos(inventario, pedidos, siguiente_id):
    while True:
        print('\nPEDIDOS\n1. Registrar pedido\n2. Mostrar pedidos\n3. Editar pedido\n4. Eliminar pedido\n0. Volver')
        opcion = leer_entero('Seleccione una opción: ', 0, 4)
        try:
            if opcion == 0:
                return siguiente_id
            if opcion == 1:
                if not inventario:
                    print('Primero registre un producto en el menú de inventario.')
                    continue
                mostrar_productos(inventario)
                cliente = leer_texto('Cliente: ')
                codigo = leer_texto('Código del producto solicitado: ')
                cantidad = leer_entero('Unidades del pedido: ', 1)
                pedido = registrar_pedido(inventario, pedidos, siguiente_id, cliente, codigo, cantidad)
                siguiente_id += 1
                print(f'Pedido {pedido["id"]} registrado correctamente. Total {calcular_total_pedido(pedido):.2f} {MONEDA}.')
            elif opcion == 2:
                mostrar_pedidos(pedidos)
            elif opcion == 3:
                identificador = leer_entero('Número del pedido a editar: ', 1)
                anterior = obtener_pedido(pedidos, identificador)
                print('Presione Enter para conservar un valor.')
                cliente = leer_texto(f'Cliente [{anterior["cliente"]}]: ', anterior['cliente'])
                codigo = leer_texto(f'Producto [{anterior["codigo"]}]: ', anterior['codigo'])
                cantidad = leer_entero(f'Cantidad [{anterior["cantidad"]}]: ', 1, actual=anterior['cantidad'])
                pedido = editar_pedido(inventario, pedidos, identificador, cliente, codigo, cantidad)
                print(f'Pedido {pedido["id"]} actualizado correctamente. Total {calcular_total_pedido(pedido):.2f} {MONEDA}.')
            elif opcion == 4:
                identificador = leer_entero('Número del pedido a eliminar: ', 1)
                obtener_pedido(pedidos, identificador)
                if confirmar(f'¿Cancelar el pedido {identificador} y devolver sus unidades al inventario?'):
                    eliminar_pedido(inventario, pedidos, identificador)
                    print(f'Pedido {identificador} eliminado. Sus unidades volvieron al inventario.')
                else:
                    print('Eliminación cancelada.')
        except ValueError as error:
            print(f'Error: {error}')


def principal() -> None:
    inventario = []
    pedidos = []
    siguiente_id = 1
    print('GESTIÓN DE PEDIDOS E INVENTARIO')
    print('Los pedidos reservan stock y todos los datos se mantienen durante esta sesión.')
    try:
        while True:
            print('\nMENÚ PRINCIPAL\n1. Inventario\n2. Pedidos\n0. Salir')
            opcion = leer_entero('Seleccione una opción: ', 0, 2)
            if opcion == 0:
                print('Sesión finalizada. Los datos de esta ejecución no se guardan en disco.')
                return
            if opcion == 1:
                menu_inventario(inventario, pedidos)
            else:
                siguiente_id = menu_pedidos(inventario, pedidos, siguiente_id)
    except (EOFError, KeyboardInterrupt):
        print('\nSesión interrumpida. Los cambios de esta ejecución no se guardan en disco.')


# Cada búsqueda en una lista requiere O(N) tiempo y el acceso por índice O(1),
# mientras append tiene costo amortizado O(1) y eliminar con pop puede desplazar
# registros posteriores en O(N), con memoria O(P + Q) para P productos y Q pedidos.
# Separar las operaciones permite cambiar la interfaz o la forma de almacenar datos
# sin reescribir las validaciones, conservando aquí las listas como pide la actividad.

if __name__ == '__main__':
    principal()
