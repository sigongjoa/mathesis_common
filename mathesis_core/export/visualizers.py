from typing import Dict, Any, List
import logging
import matplotlib.pyplot as plt
import os
import uuid

logger = logging.getLogger(__name__)

class ChartBuilder:
    """
    Builder for Matplotlib charts
    """
    def __init__(self, output_dir: str = "/tmp"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure Korean Font
        import matplotlib.font_manager as fm
        # check if NanumGothic is available
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if os.path.exists(font_path):
            prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = prop.get_name()
            # Also set for overall rcParams just in case
            plt.rcParams['font.sans-serif'] = [prop.get_name()]
            # For minus sign
            plt.rcParams['axes.unicode_minus'] = False
        else:
            logger.warning(f"NanumGothic font not found at {font_path}")
            # Try generic
            plt.rcParams['font.sans-serif'] = ['NanumGothic', 'Malgun Gothic', 'Dotum', 'AppleGothic', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False

    def create_assessment_pie_chart(self, title: str, data: Dict[str, float]) -> str:
        """
        Creates a pie chart for assessment ratios (e.g. {'Exam': 60, 'Performance': 40}).
        Returns the path to the saved image.
        """
        try:
            labels = list(data.keys())
            sizes = list(data.values())
            
            plt.figure(figsize=(8, 6))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
            plt.title(title)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            
            filename = f"chart_{uuid.uuid4().hex[:8]}.png"
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path)
            plt.close()
            
            logger.info(f"Generated assessment chart: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            return ""

    def create_achievement_chart(self, stats: Any) -> str:
        # Placeholder for matplotlib code
        logger.info("Generated achievement chart")
        return "/tmp/mock_chart_achievement.png"

    def create_curriculum_distribution(self, data: Any) -> str:
        # Placeholder
        logger.info("Generated curriculum chart")
        return "/tmp/mock_chart_curriculum.png"

class KGVisualizer:
    """
    Visualizer for Knowledge Graph
    """
    def render_graph(self, school_code: str) -> str:
        # Placeholder for pyvis/networkx
        logger.info(f"Generated KG visualization for {school_code}")
        return "/tmp/mock_kg_school.png"
