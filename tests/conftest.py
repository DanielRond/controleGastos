"""Configuração compartilhada dos testes.

Perfil do Hypothesis: o gerador de documentos é composto e a verificação
`too_slow` oscila conforme a carga da máquina (falhou 1 em 25 execuções,
sem relação com a lógica). Sem prazo por exemplo e sem essa verificação,
as propriedades ficam determinísticas quanto a tempo.
"""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "controlegastos",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("controlegastos")
