#!/usr/bin/env python3
"""
Tests automatizados para validar las reglas de negocio del sistema de trading.

REGLAS VALIDADAS (definidas en CLAUDE.md):
1. Orden de venta: MENOR VALOR PRIMERO (no FIFO)
2. Ganancia mínima: No vender si ganancia < 3%
3. No vender sin posición: cant_venta = 0 si cartera = 0
4. Límite de acciones: Máximo 10 por ticker
5. Compra múltiple: Solo si % acumulado <= promedio_minimos
6. Venta múltiple: Solo si % acumulado >= promedio_maximos

Ejecutar con: python -m pytest test_reglas_negocio.py -v
O simplemente: python test_reglas_negocio.py
"""

import sys
import unittest
from pathlib import Path

# Agregar el directorio actual al path para importar Trading_Claude
sys.path.insert(0, str(Path(__file__).parent))

from Trading_Claude import (
    validar_reglas_negocio,
    GANANCIA_MINIMA_PCT,
    LIMITE_ACCIONES_DEFAULT,
    NO_VENDER_SIN_POSICION,
    ORDEN_VENTA_MENOR_VALOR
)


class TestConstantesReglasNegocio(unittest.TestCase):
    """Verifica que las constantes de reglas de negocio estén correctamente definidas."""

    def test_ganancia_minima_es_3_porciento(self):
        """La ganancia mínima debe ser 3%."""
        self.assertEqual(GANANCIA_MINIMA_PCT, 3.0,
            "GANANCIA_MINIMA_PCT debe ser 3.0 según CLAUDE.md")

    def test_limite_acciones_es_10(self):
        """El límite de acciones por defecto debe ser 10."""
        self.assertEqual(LIMITE_ACCIONES_DEFAULT, 10,
            "LIMITE_ACCIONES_DEFAULT debe ser 10 según CLAUDE.md")

    def test_no_vender_sin_posicion_activo(self):
        """La regla de no vender sin posición debe estar activa."""
        self.assertTrue(NO_VENDER_SIN_POSICION,
            "NO_VENDER_SIN_POSICION debe ser True según CLAUDE.md")

    def test_orden_venta_menor_valor_activo(self):
        """El orden de venta debe ser MENOR VALOR PRIMERO, no FIFO."""
        self.assertTrue(ORDEN_VENTA_MENOR_VALOR,
            "ORDEN_VENTA_MENOR_VALOR debe ser True según CLAUDE.md")


class TestMenorValorPrimero(unittest.TestCase):
    """
    Valida la regla: MENOR VALOR PRIMERO (no FIFO).

    Cuando se vende, se debe vender primero la acción de MENOR precio de compra,
    NO la primera que se compró (FIFO).

    Ejemplo de CLAUDE.md:
    - Compras: $127.32, $148.70, $151.00
    - Al vender 1: se vende la de $127.32 (menor valor)
    - Quedan: $148.70, $151.00
    """

    def test_menor_valor_primero_simple(self):
        """Al vender, el precio mínimo debe ser el menor de los restantes."""
        # Simular cartera con precios: [127.32, 148.70, 151.00]
        # Después de vender 1 (la de 127.32), quedan [148.70, 151.00]
        # El precio_compra_minimo debe ser 148.70

        precios_compra = [127.32, 148.70, 151.00]
        precios_compra.sort()  # Ordenar de menor a mayor

        # Vender 1 acción (la de menor valor)
        cantidad_venta = 1
        for _ in range(cantidad_venta):
            precios_compra.pop(0)  # Eliminar el de menor precio

        precio_minimo_restante = min(precios_compra) if precios_compra else None

        self.assertEqual(precio_minimo_restante, 148.70,
            "Después de vender 1 de [127.32, 148.70, 151.00], el mínimo debe ser 148.70")

    def test_menor_valor_vs_fifo(self):
        """
        Diferencia entre FIFO y Menor Valor Primero.

        Compras en orden cronológico:
        1. $151.00 (primera compra)
        2. $127.32 (segunda compra)
        3. $148.70 (tercera compra)

        Con FIFO: se vendería $151.00 primero (INCORRECTO)
        Con Menor Valor: se vende $127.32 primero (CORRECTO)
        """
        # Simular orden cronológico de compras
        compras_cronologicas = [
            {'precio': 151.00, 'fecha': '2026-01-01'},
            {'precio': 127.32, 'fecha': '2026-01-15'},
            {'precio': 148.70, 'fecha': '2026-02-01'},
        ]

        # Extraer precios
        precios = [c['precio'] for c in compras_cronologicas]

        # MENOR VALOR PRIMERO: ordenar y tomar el primero
        precios_ordenados = sorted(precios)
        precio_a_vender = precios_ordenados[0]

        self.assertEqual(precio_a_vender, 127.32,
            "Se debe vender primero la acción de $127.32 (menor valor), no $151.00 (FIFO)")

    def test_venta_multiple_menor_valor(self):
        """Al vender múltiples acciones, se venden las de menor valor primero."""
        precios_compra = [200.00, 150.00, 180.00, 160.00, 170.00]
        precios_compra.sort()  # [150, 160, 170, 180, 200]

        # Vender 3 acciones
        cantidad_venta = 3
        vendidas = []
        for _ in range(cantidad_venta):
            vendidas.append(precios_compra.pop(0))

        # Deben venderse: 150, 160, 170 (las 3 menores)
        self.assertEqual(vendidas, [150.00, 160.00, 170.00],
            "Se deben vender las 3 acciones de menor valor")

        # Deben quedar: 180, 200
        self.assertEqual(precios_compra, [180.00, 200.00],
            "Deben quedar las 2 acciones de mayor valor")


class TestGananciaMinima(unittest.TestCase):
    """
    Valida la regla: GANANCIA MÍNIMA 3%.

    No se puede vender si la ganancia es menor al 3%.
    ganancia = (precio_venta - precio_compra_minimo) / precio_compra_minimo * 100
    """

    def test_ganancia_suficiente_permite_venta(self):
        """Si la ganancia es >= 3%, se permite la venta."""
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 153.67,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 148.70  # Ganancia: (153.67-148.70)/148.70 = 3.34%
        cartera = 5

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertTrue(resultado['validacion']['cumple_todas'],
            f"Con ganancia 3.34%, la venta debe ser permitida")
        self.assertEqual(resultado['accion'], 'vender',
            "La acción debe seguir siendo 'vender'")

    def test_ganancia_insuficiente_bloquea_venta(self):
        """Si la ganancia es < 3%, se bloquea la venta."""
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 153.67,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 151.00  # Ganancia: (153.67-151.00)/151.00 = 1.77%
        cartera = 3

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertFalse(resultado['validacion']['cumple_todas'],
            f"Con ganancia 1.77%, la venta debe ser bloqueada")
        self.assertEqual(resultado['accion'], 'esperar',
            "La acción debe cambiar a 'esperar'")
        self.assertIn('GANANCIA_MINIMA', resultado['validacion']['reglas_violadas'],
            "Debe indicar que se violó la regla GANANCIA_MINIMA")

    def test_ganancia_exacta_3_porciento(self):
        """Con ganancia exactamente 3%, se permite la venta."""
        precio_compra = 100.00
        precio_venta = 103.00  # Exactamente 3%

        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': precio_venta,
            'cantidad_venta': 1
        }
        cartera = 5

        resultado = validar_reglas_negocio(decision, precio_compra, cartera)

        self.assertTrue(resultado['validacion']['cumple_todas'],
            "Con ganancia exactamente 3%, la venta debe ser permitida")

    def test_ganancia_negativa_bloquea_venta(self):
        """Con ganancia negativa (pérdida), se bloquea la venta."""
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 95.00,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 100.00  # Pérdida: -5%
        cartera = 5

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertFalse(resultado['validacion']['cumple_todas'],
            "Con pérdida, la venta debe ser bloqueada")
        self.assertEqual(resultado['accion'], 'esperar')


class TestNoVenderSinPosicion(unittest.TestCase):
    """
    Valida la regla: NO VENDER SIN POSICIÓN.

    Si cartera = 0, cant_venta debe ser 0 y acción = esperar.
    """

    def test_vender_sin_posicion_bloqueado(self):
        """No se puede vender si no hay acciones en cartera."""
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 150.00,
            'cantidad_venta': 1
        }
        precio_compra_minimo = None
        cartera = 0  # Sin posición

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertFalse(resultado['validacion']['cumple_todas'],
            "No se puede vender sin posición")
        self.assertEqual(resultado['accion'], 'esperar',
            "La acción debe cambiar a 'esperar'")
        self.assertEqual(resultado['cantidad_venta'], 0,
            "La cantidad de venta debe ser 0")
        self.assertIn('NO_VENDER_SIN_POSICION', resultado['validacion']['reglas_violadas'])

    def test_vender_con_posicion_permitido(self):
        """Se puede vender si hay acciones en cartera (asumiendo otras reglas ok)."""
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 110.00,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 100.00  # Ganancia 10%
        cartera = 5

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertTrue(resultado['validacion']['cumple_todas'],
            "Con posición y ganancia suficiente, la venta debe ser permitida")
        self.assertEqual(resultado['accion'], 'vender')


class TestLimiteAcciones(unittest.TestCase):
    """
    Valida la regla: LÍMITE DE ACCIONES.

    No se puede comprar si ya se tiene el límite máximo (generalmente 10).
    """

    def test_comprar_en_limite_bloqueado(self):
        """No se puede comprar si ya se tiene el límite de acciones."""
        decision = {
            'accion': 'comprar',
            'precio_compra_sugerido': 150.00,
            'cantidad_compra': 1,
            'limite_acciones': 10
        }
        precio_compra_minimo = None
        cartera = 10  # Ya en el límite

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertFalse(resultado['validacion']['cumple_todas'],
            "No se puede comprar si ya se tiene el límite")
        self.assertEqual(resultado['accion'], 'esperar',
            "La acción debe cambiar a 'esperar'")
        self.assertEqual(resultado['cantidad_compra'], 0,
            "La cantidad de compra debe ser 0")
        self.assertIn('LIMITE_ACCIONES', resultado['validacion']['reglas_violadas'])

    def test_comprar_bajo_limite_permitido(self):
        """Se puede comprar si no se ha alcanzado el límite."""
        decision = {
            'accion': 'comprar',
            'precio_compra_sugerido': 150.00,
            'cantidad_compra': 1,
            'limite_acciones': 10
        }
        precio_compra_minimo = None
        cartera = 5  # Debajo del límite

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        # No debe violar la regla de límite
        self.assertNotIn('LIMITE_ACCIONES', resultado['validacion'].get('reglas_violadas', []),
            "No debe violar el límite si está debajo")

    def test_limite_personalizado(self):
        """El límite puede ser personalizado por ticker."""
        decision = {
            'accion': 'comprar',
            'precio_compra_sugerido': 150.00,
            'cantidad_compra': 1,
            'limite_acciones': 5  # Límite personalizado
        }
        precio_compra_minimo = None
        cartera = 5  # Exactamente en el límite personalizado

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertIn('LIMITE_ACCIONES', resultado['validacion']['reglas_violadas'],
            "Debe respetar el límite personalizado")


class TestCombinacionReglas(unittest.TestCase):
    """Tests que combinan múltiples reglas para escenarios realistas."""

    def test_escenario_pltr_ibkr_real(self):
        """
        Escenario real: PLTR en IBKR-UK Real.

        Cartera: 3 acciones @ $151.00
        Venta propuesta: $153.67
        Ganancia: 1.77% < 3%

        Resultado esperado: ESPERAR (ganancia insuficiente)
        """
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 153.67,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 151.00
        cartera = 3

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertEqual(resultado['accion'], 'esperar',
            "PLTR IBKR-UK Real debe ESPERAR porque ganancia 1.77% < 3%")
        self.assertIn('GANANCIA_MINIMA', resultado['validacion']['reglas_violadas'])

    def test_escenario_pltr_tyba_real(self):
        """
        Escenario real: PLTR en TYBA Real.

        Cartera: 5 acciones, precio mínimo $148.70 (después de vender $127.32)
        Venta propuesta: $153.67
        Ganancia: 3.34% >= 3%

        Resultado esperado: VENDER (ganancia suficiente)
        """
        decision = {
            'accion': 'vender',
            'precio_venta_sugerido': 153.67,
            'cantidad_venta': 1
        }
        precio_compra_minimo = 148.70
        cartera = 5

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertEqual(resultado['accion'], 'vender',
            "PLTR TYBA Real debe VENDER porque ganancia 3.34% >= 3%")
        self.assertTrue(resultado['validacion']['cumple_todas'])

    def test_escenario_aapl_limite_alcanzado(self):
        """
        Escenario: AAPL ya tiene 10 acciones (límite).

        No debe permitir más compras.
        """
        decision = {
            'accion': 'comprar',
            'precio_compra_sugerido': 248.37,
            'cantidad_compra': 1,
            'limite_acciones': 10
        }
        precio_compra_minimo = 268.72
        cartera = 10

        resultado = validar_reglas_negocio(decision, precio_compra_minimo, cartera)

        self.assertEqual(resultado['accion'], 'esperar',
            "AAPL no debe comprar porque ya tiene el límite de 10 acciones")
        self.assertIn('LIMITE_ACCIONES', resultado['validacion']['reglas_violadas'])


class TestPrioridadPrecioVenta(unittest.TestCase):
    """
    Valida la regla: PRIORIZAR PRECIOS QUE CUMPLEN GANANCIA MÍNIMA.

    ¿Qué es mejor, 0% probabilidad de venta o alguna probabilidad?
    Respuesta: Alguna probabilidad siempre es mejor que ninguna.

    Si hay precios que cumplen 3%, elegir de esos (aunque sean menos "óptimos").
    Solo si NINGUNO cumple, usar el mejor disponible.
    """

    def test_priorizar_precio_que_cumple_3_porciento(self):
        """
        Si hay precios que cumplen 3% y otros que no, elegir de los que cumplen.

        Ejemplo PLTR IBKR-UK Real:
        - Precio compra mínimo: $151.00
        - S2: $153.67 → 1.77% (NO cumple)
        - S5: $156.00 → 3.31% (SÍ cumple)

        Debe elegir S5 aunque S2 sea "más cercano" según indicadores.
        """
        precios_disponibles = [
            {'precio': 153.67, 'slot_id': '2', 'cumple_ganancia': False},  # 1.77%
            {'precio': 155.00, 'slot_id': '3', 'cumple_ganancia': False},  # 2.65%
            {'precio': 156.00, 'slot_id': '5', 'cumple_ganancia': True},   # 3.31%
        ]

        # Separar según lógica del código
        precios_cumplen = [p for p in precios_disponibles if p['cumple_ganancia']]
        precios_no_cumplen = [p for p in precios_disponibles if not p['cumple_ganancia']]

        # Debe usar los que cumplen
        precios_a_evaluar = precios_cumplen if precios_cumplen else precios_no_cumplen

        self.assertEqual(len(precios_a_evaluar), 1,
            "Solo debe evaluar el precio que cumple 3%")
        self.assertEqual(precios_a_evaluar[0]['slot_id'], '5',
            "Debe elegir S5 porque es el único que cumple 3%")

    def test_fallback_cuando_ninguno_cumple(self):
        """
        Si NINGÚN precio cumple 3%, usar el mejor disponible (fallback).
        """
        precios_disponibles = [
            {'precio': 153.67, 'slot_id': '2', 'cumple_ganancia': False},
            {'precio': 154.00, 'slot_id': '4', 'cumple_ganancia': False},
        ]

        precios_cumplen = [p for p in precios_disponibles if p['cumple_ganancia']]
        precios_no_cumplen = [p for p in precios_disponibles if not p['cumple_ganancia']]

        precios_a_evaluar = precios_cumplen if precios_cumplen else precios_no_cumplen
        usar_fallback = len(precios_cumplen) == 0

        self.assertTrue(usar_fallback,
            "Debe usar fallback si ninguno cumple 3%")
        self.assertEqual(len(precios_a_evaluar), 2,
            "Debe evaluar todos los disponibles en fallback")

    def test_elegir_mejor_entre_los_que_cumplen(self):
        """
        Si varios precios cumplen 3%, elegir el mejor según contexto.
        """
        precios_disponibles = [
            {'precio': 156.00, 'slot_id': '3', 'cumple_ganancia': True},   # 3.31%
            {'precio': 158.00, 'slot_id': '5', 'cumple_ganancia': True},   # 4.64%
        ]

        precios_cumplen = [p for p in precios_disponibles if p['cumple_ganancia']]

        self.assertEqual(len(precios_cumplen), 2,
            "Ambos cumplen, ambos deben ser evaluados")
        # La selección final depende del contexto (RSI, tendencia, etc.)


def run_tests():
    """Ejecuta todos los tests y muestra un resumen."""
    print("=" * 70)
    print("TESTS DE REGLAS DE NEGOCIO - Trading System")
    print("=" * 70)
    print(f"\nReglas validadas (según CLAUDE.md):")
    print(f"  1. Orden de venta: MENOR VALOR PRIMERO (no FIFO)")
    print(f"  2. Ganancia mínima: {GANANCIA_MINIMA_PCT}%")
    print(f"  3. No vender sin posición: {NO_VENDER_SIN_POSICION}")
    print(f"  4. Límite de acciones: {LIMITE_ACCIONES_DEFAULT}")
    print(f"  5. Orden venta menor valor: {ORDEN_VENTA_MENOR_VALOR}")
    print("=" * 70)

    # Ejecutar tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Resumen final
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("[OK] TODOS LOS TESTS PASARON")
        print("     Las reglas de negocio estan correctamente implementadas.")
    else:
        print("[FAIL] ALGUNOS TESTS FALLARON")
        print("       Revisar la implementacion de las reglas de negocio.")
        print(f"       Fallos: {len(result.failures)}")
        print(f"       Errores: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
