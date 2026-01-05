Parece que tiene sentido restringir mucho la inversion a periodos de crisis/caidas. La comparativa es mas justa porque si cogemos periodos largos, los periodos de tiempo en los que la estrategia no se usa y el indice crece, el escenario base lo va a hacer mucho mejor, pero en nuestro caso real no vamos a dejar de estar invertidos en el indice por utilizar la estrategia (pignoracion). Aunque siendo estrictos da igual que el dinero venga de una pignoracion, el escenario base seria el mismo, pero sí que habría que estar descontando el tipo de interes de la pignoracion por cada dia que estamos invertidos.



### Configuraciones en fase de prueba

```python
default_thresholds_df = pd.DataFrame([
    {"drawdown": -0.10, "buy_pct": 0.05, "asset": "x2"},
    {"drawdown": -0.15, "buy_pct": 0.12, "asset": "x2"},
    {"drawdown": -0.20, "buy_pct": 0.20, "asset": "x2"},
    {"drawdown": -0.25, "buy_pct": 0.10, "asset": "x3"},
    {"drawdown": -0.30, "buy_pct": 0.20, "asset": "x3"},
    {"drawdown": -0.35, "buy_pct": 0.30, "asset": "x3"},
    {"drawdown": -0.40, "buy_pct": 0.40, "asset": "x3"},
    {"drawdown": -0.50, "buy_pct": 0.50, "asset": "x3"},
    {"drawdown": -0.60, "buy_pct": 0.60, "asset": "x3"},
    {"drawdown": -0.70, "buy_pct": 0.70, "asset": "x3"},
    {"drawdown": -0.80, "buy_pct": 0.80, "asset": "x3"}
])
```



```python
default_thresholds_df = pd.DataFrame([
    {"drawdown": -0.10, "buy_pct": 0.05, "asset": "x2"},
    {"drawdown": -0.15, "buy_pct": 0.15, "asset": "x2"},
    {"drawdown": -0.20, "buy_pct": 0.30, "asset": "x2"},
    {"drawdown": -0.30, "buy_pct": 0.10, "asset": "x3"},
    {"drawdown": -0.40, "buy_pct": 0.30, "asset": "x3"},
    {"drawdown": -0.50, "buy_pct": 0.50, "asset": "x3"},
    {"drawdown": -0.60, "buy_pct": 0.70, "asset": "x3"},
])
```

```python
default_thresholds_df = pd.DataFrame([
    {"drawdown": -0.10, "buy_pct": 0.05, "asset": "x2"},
    {"drawdown": -0.15, "buy_pct": 0.15, "asset": "x2"},
    {"drawdown": -0.20, "buy_pct": 0.30, "asset": "x2"},
    {"drawdown": -0.30, "buy_pct": 0.10, "asset": "x3"},
    {"drawdown": -0.40, "buy_pct": 0.30, "asset": "x3"},
    {"drawdown": -0.50, "buy_pct": 0.50, "asset": "x3"},
    {"drawdown": -0.60, "buy_pct": 0.70, "asset": "x3"},
])
```





Se podría probar con el auto exigiendo el doble de rentabilidad a ver que tal.

