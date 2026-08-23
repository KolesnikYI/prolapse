"""Калькулятор вероятности рецидива пролапса органов тазового дна.

Состоит из двух классов:
    - CalculatorCore: содержит константы и механизм рассчетов.
    - CalculatorApp: GUI надстройка
РАссчет выполняется для фиксированных временных промежутков: 1, 3, 5 лет.
"""

import tkinter as tk
import math

from tkinter import ttk


class CalculatorCore:
    """Калькулятор вероятности рецидива пролапса ОТД на 1, 3, 5 лет."""

    # Полученные коэффициенты из модели регрессии Кокса
    B_CONSTIPATION = 0.59285293460
    B_NATIVE = -0.01366890591
    B_MESH = -0.79573088347
    B_VENOUS = 0.42729109467
    B_WORK = -0.05658684330

    # Базовая кумулятивная функция для 1, 3, 5 лет относительно грыж ПБС
    CUMHAZ_HERNIA = (0.11806342850, 0.35188247650, 0.86190281540)
    CUMHAZ_NO_HERNIA = (0.09519154307, 0.25235898612, 0.56782907502)

    def __init__(
        self,
        constipation: bool,  # Наличие хронических заболеваний ЖКТ
        mesh_repair: bool,  # Пластика с использованием MESH-импланта
        venous_insufficiency: bool,  # Наличие ХВН
        heavy_physical_work: bool,  # Тяжелые условия физического труда
        abdominal_wall_hernia: bool,  # Наличие грыжи передней брюшной стенки
    ) -> None:
        self.constipation = constipation
        self.mesh_repair = mesh_repair
        self.venous_insufficiency = venous_insufficiency
        self.heavy_physical_work = heavy_physical_work
        self.abdominal_wall_hernia = abdominal_wall_hernia
        self.native_tissue_repair = not self.mesh_repair
        self.TIMES = (1, 3, 5)

        # Рассчет кумулятивного риска относительно грыж ПБС
        self._baseline_cumulative_hazard = (
            self.CUMHAZ_HERNIA
            if self.abdominal_wall_hernia
            else self.CUMHAZ_NO_HERNIA
        )

    def relapse_probabilities(self) -> dict:
        """Рассчет и сохранение вероятностей рецидива."""
        log_hr = (
            self.B_CONSTIPATION * self.constipation
            + self.B_NATIVE * (not self.mesh_repair)
            + self.B_MESH * self.mesh_repair
            + self.B_VENOUS * self.venous_insufficiency
            + self.B_WORK * self.heavy_physical_work
        )
        cumhaz = (
            self.CUMHAZ_HERNIA
            if self.abdominal_wall_hernia
            else self.CUMHAZ_NO_HERNIA
        )
        return {
            t: 1 - math.exp(-math.exp(log_hr) * c)
            for t, c in zip(self.TIMES, cumhaz)
        }


class CalculatorApp(tk.Tk):
    """GUI-надстройка над CalculatorCore."""

    WIDTH, HEIGHT = 560, 540
    FONT_FAMILY = "TkDefaultFont"
    FONT_SIZE = 12

    INSTRUCTION_TOP = (
        "Отметьте факторы, относящиеся к пациенту — вероятность рецидива "
        "пересчитывается автоматически при изменении любого флажка."
    )
    DISCLAIMER = (
        "Результат является статистической оценкой по модели регрессии Кокса "
        "и не заменяет клиническое решение врача."
    )

    FIELDS = [
        ("constipation", "Хронические заболевания ЖКТ"),
        ("mesh_repair", "Пластика с использованием MESH-импланта"),
        ("venous_insufficiency", "Хроническая венозная недостаточность"),
        ("heavy_physical_work", "Тяжёлые условия физического труда"),
        ("abdominal_wall_hernia", "Грыжи передней брюшной стенки"),
    ]

    def __init__(self) -> None:
        super().__init__()

        # Настройки окна
        self.title("Калькулятор рецидива пролапса ОТД")
        self.resizable(False, False)
        self._center_window()

        # Настройки шрифтов
        style = ttk.Style(self)
        base_font = (self.FONT_FAMILY, self.FONT_SIZE)
        style.configure("TLabel", font=base_font)
        style.configure("TCheckbutton", font=base_font)
        style.configure("TLabelframe", font=base_font)
        style.configure(
            "Bold.TLabelframe.Label",
            font=(self.FONT_FAMILY, self.FONT_SIZE, "bold"),
        )

        # Положение инструкции
        ttk.Label(
            self,
            text=self.INSTRUCTION_TOP,
            wraplength=self.WIDTH - 48,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(14, 4))

        # Блок «Факторы риска»
        factors = ttk.LabelFrame(
            self, text="Факторы риска", style="Bold.TLabelframe"
        )
        factors.pack(fill="x", padx=16, pady=6)

        # Словарь со значениями факторов риска в boolean-формате
        self._vars: dict[str, tk.BooleanVar] = {}
        for key, label in self.FIELDS:
            var = tk.BooleanVar(value=False)
            self._vars[key] = var
            ttk.Checkbutton(
                factors,
                text=label,
                variable=var,
                command=self._recalc,
            ).pack(anchor="w", padx=12, pady=2)

        # Блок «Вероятность рецидива»
        results = ttk.LabelFrame(
            self, text="Вероятность рецидива", style="Bold.TLabelframe"
        )
        results.pack(fill="x", padx=16, pady=6)

        # Результаты
        self._result = ttk.Label(results, justify="left")
        self._result.pack(anchor="w", padx=12, pady=8)

        # Дисклеймер
        ttk.Label(
            self,
            text=self.DISCLAIMER,
            wraplength=self.WIDTH - 48,
            justify="left",
            foreground="#555555",
        ).pack(anchor="w", padx=16, pady=(4, 14))

        # Первичный расчёт
        self._recalc()

    def _center_window(self) -> None:
        """Центрирует окно на экране, исходя из текущих размеров монитора."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.WIDTH) // 2
        y = (screen_h - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _recalc(self) -> None:
        """Собирает значения чекбоксов, передаёт в ядро, выводит результат."""
        inputs = {key: var.get() for key, var in self._vars.items()}
        core = CalculatorCore(**inputs)

        probs = core.relapse_probabilities()
        self._result["text"] = "\n".join(
            f"через {years} г.: {p:.1%}" for years, p in probs.items()
        )


if __name__ == "__main__":
    CalculatorApp().mainloop()
