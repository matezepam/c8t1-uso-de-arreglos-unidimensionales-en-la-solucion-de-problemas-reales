# Uso de arreglos unidimensionales en la solución de problemas reales

El programa permite gestionar productos y pedidos desde la consola mediante dos listas unidimensionales, utilizando funciones para registrar, consultar, editar y eliminar registros y manteniendo la relación entre los pedidos y las unidades disponibles para evitar reservas sin stock.

## Ejecución

El archivo principal es `GESTION DE PEDIDOS E INVENTARIO.py` y utiliza únicamente la biblioteca estándar de Python, por lo que puede ejecutarse desde una terminal ubicada en esta carpeta sin instalar paquetes adicionales.

```bash
python "GESTION DE PEDIDOS E INVENTARIO.py"
```

El menú principal permite entrar al inventario, gestionar pedidos o salir, mientras cada submenú incluye registro, listado, edición y eliminación, con la opción cero para volver y la posibilidad de conservar un campo durante la edición presionando Enter.

Los datos se mantienen durante la sesión y no se guardan en disco, de modo que cerrar el programa termina ese registro temporal y una nueva ejecución comienza sin productos ni pedidos, como corresponde al alcance básico de esta actividad.

## Uso de arreglos unidimensionales

`inventario` y `pedidos` son las listas que almacenan los datos del sistema y cada posición contiene un registro con campos identificados mediante un diccionario, conservando una sola dimensión de acceso para recorrer los productos o los pedidos sin utilizar matrices ni una base de datos como almacenamiento principal.

Las funciones de búsqueda recorren índices desde cero hasta la longitud menos uno y devuelven la posición del registro o menos uno si no existe, permitiendo leer y modificar el elemento correcto sin confundir su índice con el código del producto o el número del pedido.

El registro usa `append`, la edición modifica el registro localizado y la eliminación usa `pop`, por lo que se muestran las operaciones de escritura, lectura e iteración de la clase y también el desplazamiento de posiciones que puede producirse al quitar un elemento.

Las listas de Python pueden crecer dinámicamente y almacenan referencias, así que no se afirma que todos los valores de sus diccionarios estén físicamente contiguos en memoria ni que se comporten como un arreglo estático de números.

## Organización del código

Las operaciones reciben las listas como parámetros y contienen las reglas de negocio, mientras los menús se encargan de solicitar datos y mostrar resultados para que una futura interfaz pueda utilizar las mismas funciones sin repetir las validaciones.

| Acción | Inventario | Pedidos |
|---|---|---|
| Registrar | `registrar_producto` | `registrar_pedido` |
| Mostrar | `mostrar_productos` | `mostrar_pedidos` |
| Editar | `editar_producto` | `editar_pedido` |
| Eliminar | `eliminar_producto` | `eliminar_pedido` |

`buscar_producto`, `buscar_pedido`, `obtener_producto` y `obtener_pedido` concentran la localización de registros para evitar búsquedas implementadas de forma diferente en cada acción, mientras `calcular_total_pedido` mantiene separado el cálculo del importe y las funciones de entrada vuelven a preguntar cuando el dato no es válido.

## Reglas de inventario y pedidos

Cada producto tiene código, nombre, stock disponible y precio, con códigos normalizados para evitar duplicados por diferencias de espacios o mayúsculas y nombres que tampoco pueden repetirse en otro producto, manteniendo el código fijo al editar para no romper su relación con los pedidos existentes.

El stock debe ser un entero no negativo y el precio debe ser positivo, con un límite comercial de 999999999.99 USD y como máximo dos decimales, utilizando `Decimal` para conservar centavos sin errores binarios y admitiendo punto o coma como separador decimal sin separadores de miles.

Cada pedido reserva un solo producto y contiene identificador, cliente, cantidad, precio unitario y fechas completas de creación y actualización, descontando unidades únicamente después de validar la solicitud y conservando el precio acordado aunque posteriormente cambie el catálogo.

Si una edición mantiene el producto se conserva ese precio y se calcula la disponibilidad incluyendo la reserva anterior, mientras un cambio de producto devuelve las unidades al original y utiliza el stock y precio actuales del nuevo artículo, comprobando todo antes de aplicar los movimientos para no dejar cambios parciales ante un rechazo.

Eliminar un pedido equivale a cancelarlo y devuelve sus unidades al inventario, mientras un producto con pedidos activos no puede eliminarse hasta cancelar esas reservas para evitar registros huérfanos y garantizar que sus unidades puedan restituirse.

Los identificadores de pedido aumentan después de cada registro correcto y no se reutilizan al eliminar durante la sesión, de modo que un pedido conserva su número aunque cambie la posición que ocupa dentro de la lista.

Modificar el stock de un producto significa corregir sus unidades disponibles, no el total que incluye reservas, por lo que el menú lo indica y mantiene las cantidades de pedidos separadas de ese valor.

## Validaciones

El programa rechaza texto donde se esperan enteros, cantidades negativas, pedidos de cero unidades, precios inválidos, códigos inexistentes y solicitudes sin stock suficiente, recuperando el menú sin detenerse con una traza de error y solicitando confirmación antes de eliminar registros.

También reconoce listas vacías, impide registrar un pedido sin catálogo y permite finalizar ante fin de entrada o interrupción del teclado, con fechas que incluyen día y zona horaria y comprobaciones que evitan editar un pedido con un instante anterior a su creación o a su última actualización.

## Rendimiento y posibilidad de ampliación

Buscar en una lista requiere O(N) tiempo y acceder a una posición conocida O(1), mientras `append` tiene costo amortizado O(1) y `pop` puede desplazar los elementos posteriores en O(N), con memoria O(P + Q) para P productos y Q pedidos y sin copias completas de las colecciones en cada operación.

Registrar o editar un producto cuesta O(P) por las búsquedas de identidad y duplicados, mientras las operaciones de pedidos y la eliminación de productos relacionados cuestan O(P + Q), evitando buscar nombres de producto por cada fila al mostrar pedidos y utilizando el código que ya contiene su registro.

La separación de operaciones permite añadir búsquedas, reportes o persistencia manteniendo la interfaz de las funciones, aunque para catálogos grandes convendría revisar la estructura de búsqueda y su costo lineal en lugar de afirmar que una lista ofrece consultas constantes por código.

## Evidencias de ejecución

Las siguientes capturas muestran el programa en funcionamiento desde el registro inicial hasta la verificación final del inventario, conservando las entradas y los resultados de la sesión para comprobar las operaciones solicitadas.

### Inicio y acceso al inventario

La ejecución comienza desde la terminal y permite entrar al inventario mediante el menú principal para consultar las acciones disponibles sin modificar todavía los registros.

![Inicio y acceso al inventario](IMAGENES/1.%20ENTRAR%20INVENTARIO.png)

### Registro del primer producto

El producto P01 se registra como Tornillos con diez unidades y precio de 1.10 USD, mostrando la confirmación antes de volver al menú para continuar con otras operaciones.

![Registro del primer producto](IMAGENES/2.%20REGISTRAR%20PRODUCTO.png)

### Listado y edición de productos

El listado muestra P01 y P02 antes de editar el primero como Tornillos Largos con doce unidades y precio de 1.25 USD, permitiendo comparar la lectura inicial con el resultado de la modificación.

![Listado y edición de productos](IMAGENES/3.%20REGISTRAR%20OTRO%20PRODUCTO.png)

### Registro de un pedido

El cliente Paulo solicita tres unidades de P01 y el programa confirma el pedido 1 por 3.75 USD, reservando la cantidad solicitada a partir de las existencias disponibles.

![Registro de un pedido](IMAGENES/4.%20REGISTRAR%20UN%20PEDIDO.png)

### Edición de un pedido

El pedido 1 cambia al cliente Paulo Salazar y al producto P02 con cuatro unidades, actualizando su total a 10.00 USD después de comprobar que puede devolver la reserva anterior y aplicar la nueva.

![Edición de un pedido](IMAGENES/5.%20EDITAR%20UN%20PEDIDO.png)

### Protección de un producto con pedidos activos

El intento de eliminar P02 se rechaza porque todavía tiene un pedido activo, evitando que desaparezca el producto necesario para mantener la reserva y devolver sus unidades si se cancela.

![Protección de un producto con pedidos activos](IMAGENES/6.%20INTENTAR%20ELIMINAR%20UN%20PRODUCTO%20CON%20CLIENTES.png)

### Cancelación de un pedido

La eliminación del pedido 1 requiere confirmación y devuelve las unidades al inventario, dejando el producto disponible para una posterior eliminación sin relaciones pendientes.

![Cancelación de un pedido](IMAGENES/7.%20SEGMENTO%20PARA%20LA%20ELIMINACION%20DE%20PEDIDOS.png)

### Eliminación del producto y verificación final

Después de cancelar el pedido se elimina P02 y el listado final conserva únicamente P01 con doce unidades y precio de 1.25 USD, mostrando que la devolución de stock y la eliminación se realizaron en el orden previsto.

![Eliminación del producto y verificación final](IMAGENES/8.%20VERIFICACION%20DEL%20INVENTARIO.png)

## Pruebas

Las 28 pruebas de `PRUEBAS.py` comprueban las operaciones sobre listas, el control del stock, la conservación del precio, los identificadores después de borrar, las fechas y las entradas por teclado, incluyendo cambios rechazados sin alteraciones parciales y confirmaciones canceladas que deben mantener los datos anteriores.

```bash
python PRUEBAS.py
```
