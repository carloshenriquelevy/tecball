import pytest
from app.scoring import calculate_bet_points, calculate_special_bet_points
from app.models import Stage


# ── calculate_bet_points — fase de grupos ────────────────────────────────────

class TestGroupStage:
    def test_placar_exato(self):
        assert calculate_bet_points(Stage.GROUP, 2, 1, 2, 1) == 10

    def test_empate_exato(self):
        assert calculate_bet_points(Stage.GROUP, 1, 1, 1, 1) == 10

    def test_vencedor_e_diferenca_corretos(self):
        # 3-1 vs 2-0: ambos casa vence por 2
        assert calculate_bet_points(Stage.GROUP, 3, 1, 2, 0) == 7

    def test_empate_diferente_placar(self):
        # qualquer empate vs empate tem diferença 0=0 → 7 pts
        assert calculate_bet_points(Stage.GROUP, 1, 1, 2, 2) == 7

    def test_vencedor_correto_diferenca_errada(self):
        assert calculate_bet_points(Stage.GROUP, 1, 0, 3, 0) == 5

    def test_resultado_errado(self):
        assert calculate_bet_points(Stage.GROUP, 0, 1, 1, 0) == 0

    def test_empate_vs_vitoria(self):
        assert calculate_bet_points(Stage.GROUP, 1, 1, 2, 0) == 0

    def test_placar_zero_zero_exato(self):
        assert calculate_bet_points(Stage.GROUP, 0, 0, 0, 0) == 10


# ── calculate_bet_points — mata-mata ─────────────────────────────────────────

class TestPlayoffStage:
    @pytest.mark.parametrize("stage", [Stage.R32, Stage.R16, Stage.QF, Stage.SF, Stage.THIRD, Stage.FINAL])
    def test_placar_exato(self, stage):
        assert calculate_bet_points(stage, 2, 1, 2, 1) == 15

    @pytest.mark.parametrize("stage", [Stage.R16, Stage.QF, Stage.SF, Stage.FINAL])
    def test_vencedor_correto_placar_errado(self, stage):
        assert calculate_bet_points(stage, 1, 0, 3, 1) == 8

    @pytest.mark.parametrize("stage", [Stage.R16, Stage.QF])
    def test_vencedor_errado(self, stage):
        assert calculate_bet_points(stage, 0, 1, 1, 0) == 0

    def test_final_placar_exato(self):
        assert calculate_bet_points(Stage.FINAL, 1, 0, 1, 0) == 15

    def test_final_vencedor_errado(self):
        assert calculate_bet_points(Stage.FINAL, 0, 1, 1, 0) == 0


# ── calculate_special_bet_points ─────────────────────────────────────────────

class TestSpecialBet:
    def test_tudo_correto(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 1, 2, 3, 4) == 75  # 30+20+15+10

    def test_tudo_errado(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 5, 6, 7, 8) == 0

    def test_apenas_campeao(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 1, 6, 7, 8) == 30

    def test_apenas_vice(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 5, 2, 7, 8) == 20

    def test_apenas_terceiro(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 5, 6, 3, 8) == 15

    def test_apenas_quarto(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 5, 6, 7, 4) == 10

    def test_campeao_e_vice(self):
        assert calculate_special_bet_points(1, 2, 3, 4, 1, 2, 7, 8) == 50  # 30+20

    def test_nenhum_palpite_feito(self):
        assert calculate_special_bet_points(None, None, None, None, 1, 2, 3, 4) == 0

    def test_palpite_parcial_none(self):
        # só campeão preenchido, acertou
        assert calculate_special_bet_points(1, None, None, None, 1, 2, 3, 4) == 30
