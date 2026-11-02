# Las pruebas utilizan el archivo real sin iniciar el menú para comprobar primero
# las operaciones sobre listas y después las entradas del usuario, manteniendo
# separados los errores de negocio y los problemas de lectura por teclado.

import importlib.util
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

RUTA = Path(__file__).resolve().parent / 'GESTION DE PEDIDOS E INVENTARIO.py'
especificacion = importlib.util.spec_from_file_location('gestion', RUTA)
gestion = importlib.util.module_from_spec(especificacion)
especificacion.loader.exec_module(gestion)


class InventarioYPedidos(unittest.TestCase):
    def setUp(self):
        self.inventario = []
        self.pedidos = []
        self.momento = datetime(2026, 11, 1, 12, tzinfo=timezone(timedelta(hours=-5)))
        gestion.registrar_producto(self.inventario, 'P01', 'Tornillos', 10, '1.10')
        gestion.registrar_producto(self.inventario, 'P02', 'Tuercas', 8, '2.50')

    def crear_pedido(self, cantidad=3, codigo='P01', identificador=1):
        return gestion.registrar_pedido(self.inventario, self.pedidos, identificador,
                                        'Ana', codigo, cantidad, self.momento)

    def test_listas_unidimensionales_y_busqueda(self):
        self.assertIsInstance(self.inventario, list)
        self.assertIsInstance(self.pedidos, list)
        self.assertTrue(all(isinstance(p, dict) for p in self.inventario))
        self.assertEqual(gestion.buscar_producto(self.inventario, ' p01 '), 0)
        self.assertEqual(gestion.buscar_producto(self.inventario, 'P02'), 1)
        self.assertEqual(gestion.buscar_producto(self.inventario, 'ausente'), -1)

    def test_producto_sin_stock(self):
        producto = gestion.registrar_producto(self.inventario, 'P03', 'Arandelas', 0, '0.25')
        self.assertEqual(producto['stock'], 0)
        self.assertEqual(len(self.inventario), 3)

    def test_codigos_y_nombres_no_duplicados(self):
        antes = deepcopy(self.inventario)
        for codigo, nombre in ((' p01 ', 'Otro'), ('P03', ' tornillos '), ('P03', 'TORNILLOS')):
            with self.assertRaises(ValueError):
                gestion.registrar_producto(self.inventario, codigo, nombre, 1, '1')
        self.assertEqual(self.inventario, antes)

    def test_validar_cantidades_y_precios(self):
        for cantidad in (-1, 1.5, True, '2'):
            with self.assertRaises(ValueError):
                gestion.registrar_producto(self.inventario, 'P03', 'Otro', cantidad, '1')
        for precio in ('0', '-1', '0.001', 'NaN', 'Infinity', 'abc', 0.1):
            with self.assertRaises(ValueError):
                gestion.registrar_producto(self.inventario, 'P03', 'Otro', 1, precio)
        self.assertEqual(gestion.validar_precio('1,25'), Decimal('1.25'))

    def test_editar_producto_sin_cambiar_identidad(self):
        referencia = self.inventario[0]
        gestion.editar_producto(self.inventario, 'P01', 'Tornillos largos', 12, '1.50')
        self.assertIs(self.inventario[0], referencia)
        self.assertEqual(referencia['codigo'], 'P01')
        self.assertEqual((referencia['nombre'], referencia['stock'], referencia['precio']),
                         ('Tornillos largos', 12, Decimal('1.50')))

    def test_edicion_producto_rechazada_no_cambia_datos(self):
        antes = deepcopy(self.inventario)
        for nombre, stock, precio in (('Tuercas', 9, '2'), ('Nuevo', -1, '2'), ('Nuevo', 9, '-2')):
            with self.assertRaises(ValueError):
                gestion.editar_producto(self.inventario, 'P01', nombre, stock, precio)
            self.assertEqual(self.inventario, antes)

    def test_eliminar_producto_desplaza_posiciones(self):
        eliminado = gestion.eliminar_producto(self.inventario, self.pedidos, 'P01')
        self.assertEqual(eliminado['codigo'], 'P01')
        self.assertEqual(gestion.buscar_producto(self.inventario, 'P02'), 0)
        with self.assertRaises(ValueError): gestion.obtener_producto(self.inventario, 'P01')

    def test_pedido_descuenta_y_calcula_total(self):
        pedido = self.crear_pedido()
        self.assertEqual(self.inventario[0]['stock'], 7)
        self.assertEqual(gestion.calcular_total_pedido(pedido), Decimal('3.30'))
        self.assertEqual(pedido['creado_en'], self.momento)
        self.assertIs(gestion.obtener_pedido(self.pedidos, 1), pedido)

    def test_pedido_con_todo_el_stock(self):
        self.crear_pedido(cantidad=10)
        self.assertEqual(self.inventario[0]['stock'], 0)
        with self.assertRaises(ValueError): self.crear_pedido(cantidad=1, identificador=2)
        self.assertEqual(len(self.pedidos), 1)

    def test_pedido_invalido_no_reserva(self):
        antes = deepcopy(self.inventario)
        for cantidad, codigo in ((0, 'P01'), (-1, 'P01'), (11, 'P01'), (1, 'P99')):
            with self.assertRaises(ValueError): self.crear_pedido(cantidad, codigo)
            self.assertEqual(self.inventario, antes)
            self.assertEqual(self.pedidos, [])
        with self.assertRaises(ValueError):
            gestion.registrar_pedido(self.inventario, self.pedidos, 1, ' ', 'P01', 1, self.momento)

    def test_identificador_duplicado_no_descuenta(self):
        self.crear_pedido()
        antes = deepcopy(self.inventario)
        with self.assertRaises(ValueError): self.crear_pedido()
        self.assertEqual(self.inventario, antes)
        self.assertEqual(len(self.pedidos), 1)

    def test_precio_del_pedido_no_cambia_con_catalogo(self):
        pedido = self.crear_pedido()
        gestion.editar_producto(self.inventario, 'P01', 'Tornillos', 7, '9')
        self.assertEqual(pedido['precio_unitario'], Decimal('1.10'))
        gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana', 'P01', 4,
                              self.momento + timedelta(minutes=1))
        self.assertEqual(pedido['precio_unitario'], Decimal('1.10'))
        self.assertEqual(gestion.calcular_total_pedido(pedido), Decimal('4.40'))

    def test_editar_cantidad_usa_reserva_previa(self):
        pedido = self.crear_pedido()
        gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana Pérez', 'P01', 10,
                              self.momento + timedelta(minutes=1))
        self.assertEqual(self.inventario[0]['stock'], 0)
        self.assertEqual(pedido['cantidad'], 10)
        gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana Pérez', 'P01', 2,
                              self.momento + timedelta(minutes=2))
        self.assertEqual(self.inventario[0]['stock'], 8)

    def test_editar_producto_del_pedido_devuelve_y_reserva(self):
        pedido = self.crear_pedido()
        gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana', 'P02', 4,
                              self.momento + timedelta(minutes=1))
        self.assertEqual([p['stock'] for p in self.inventario], [10, 4])
        self.assertEqual(pedido['precio_unitario'], Decimal('2.50'))
        self.assertEqual(gestion.calcular_total_pedido(pedido), Decimal('10.00'))

    def test_edicion_pedido_rechazada_conserva_ambas_listas(self):
        self.crear_pedido()
        antes = deepcopy((self.inventario, self.pedidos))
        for codigo, cantidad in (('P01', 11), ('P02', 9), ('P99', 1), ('P01', 0)):
            with self.assertRaises(ValueError):
                gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana', codigo, cantidad,
                                      self.momento + timedelta(minutes=1))
            self.assertEqual((self.inventario, self.pedidos), antes)

    def test_bloquear_eliminacion_de_producto_reservado(self):
        self.crear_pedido()
        antes = deepcopy(self.inventario)
        with self.assertRaises(ValueError):
            gestion.eliminar_producto(self.inventario, self.pedidos, 'P01')
        self.assertEqual(self.inventario, antes)

    def test_eliminar_pedido_restituye_y_permite_borrar_producto(self):
        self.crear_pedido()
        eliminado = gestion.eliminar_pedido(self.inventario, self.pedidos, 1)
        self.assertEqual(eliminado['cantidad'], 3)
        self.assertEqual(self.inventario[0]['stock'], 10)
        self.assertEqual(self.pedidos, [])
        gestion.eliminar_producto(self.inventario, self.pedidos, 'P01')
        self.assertEqual(len(self.inventario), 1)

    def test_ids_sobreviven_a_cambios_de_indice(self):
        self.crear_pedido(1, identificador=1)
        self.crear_pedido(1, identificador=2)
        gestion.eliminar_pedido(self.inventario, self.pedidos, 1)
        self.assertEqual(gestion.buscar_pedido(self.pedidos, 2), 0)
        self.assertEqual(gestion.obtener_pedido(self.pedidos, 2)['id'], 2)

    def test_fechas_completas_y_ordenadas(self):
        self.crear_pedido()
        with self.assertRaises(ValueError):
            gestion.editar_pedido(self.inventario, self.pedidos, 1, 'Ana', 'P01', 2,
                                  self.momento - timedelta(minutes=1))
        with self.assertRaises(ValueError): gestion.obtener_momento(datetime(2026, 1, 1))

    def test_listados_vacios_y_con_datos(self):
        salida = StringIO()
        with redirect_stdout(salida):
            self.assertIsNone(gestion.mostrar_productos([]))
            self.assertIsNone(gestion.mostrar_pedidos([]))
            gestion.mostrar_productos(self.inventario)
            self.crear_pedido()
            gestion.mostrar_pedidos(self.pedidos)
        self.assertIn('No hay productos', salida.getvalue())
        self.assertIn('No hay pedidos', salida.getvalue())
        self.assertIn('3.30 USD', salida.getvalue())


class EntradaYMenu(unittest.TestCase):
    def leer(self, funcion, entradas, *argumentos, **opciones):
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            return funcion(*argumentos, **opciones)

    def test_letras_y_rangos_en_enteros(self):
        self.assertEqual(self.leer(gestion.leer_entero, ['abc', '-1', '8', '2'], 'Número: ', 0, 4), 2)
        self.assertEqual(self.leer(gestion.leer_entero, ['0', '1.5', '3'], 'Cantidad: ', 1), 3)

    def test_precio_invalido_y_coma_decimal(self):
        self.assertEqual(self.leer(gestion.leer_precio, ['abc', '-1', 'NaN', '1,25'], 'Precio: '), Decimal('1.25'))

    def test_enter_conserva_y_confirmacion(self):
        self.assertEqual(self.leer(gestion.leer_texto, [''], 'Nombre: ', 'Actual'), 'Actual')
        self.assertEqual(self.leer(gestion.leer_entero, [''], 'Stock: ', actual=5), 5)
        self.assertEqual(self.leer(gestion.leer_precio, [''], 'Precio: ', Decimal('2')), Decimal('2'))
        self.assertTrue(self.leer(gestion.confirmar, ['tal vez', 'sí'], '¿Continuar?'))
        self.assertFalse(self.leer(gestion.confirmar, ['n'], '¿Continuar?'))

    def test_menu_pedidos_no_reutiliza_identificadores(self):
        inventario, pedidos = [], []
        gestion.registrar_producto(inventario, 'P01', 'Producto', 10, '1')
        entradas = ['1', 'Ana', 'P01', '2', '4', '1', 's', '1', 'Luis', 'P01', '1', '0']
        siguiente = self.leer(gestion.menu_pedidos, entradas, inventario, pedidos, 1)
        self.assertEqual(siguiente, 3)
        self.assertEqual(pedidos[0]['id'], 2)
        self.assertEqual(inventario[0]['stock'], 9)

    def test_cancelar_borrado_no_cambia_datos(self):
        inventario, pedidos = [], []
        gestion.registrar_producto(inventario, 'P01', 'Producto', 10, '1')
        antes = deepcopy(inventario)
        self.leer(gestion.menu_inventario, ['4', 'P01', 'n', '0'], inventario, pedidos)
        self.assertEqual(inventario, antes)

    def test_principal_recupera_menu_y_sale(self):
        salida = StringIO()
        with patch('builtins.input', side_effect=['letra', '3', '0']), redirect_stdout(salida):
            gestion.principal()
        self.assertIn('Error:', salida.getvalue())
        self.assertIn('Sesión finalizada', salida.getvalue())

    def test_pedido_sin_catalogo_informa_y_permite_volver(self):
        salida = StringIO()
        with patch('builtins.input', side_effect=['1', '0']), redirect_stdout(salida):
            siguiente = gestion.menu_pedidos([], [], 1)
        self.assertEqual(siguiente, 1)
        self.assertIn('Primero registre un producto', salida.getvalue())

    def test_fin_de_entrada_no_genera_traza(self):
        salida = StringIO()
        with patch('builtins.input', side_effect=EOFError), redirect_stdout(salida):
            gestion.principal()
        self.assertIn('Sesión interrumpida', salida.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
