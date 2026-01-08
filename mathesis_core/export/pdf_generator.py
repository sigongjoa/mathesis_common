
from typing import Dict, Any, List
import logging
from ..models.school import SchoolData
from .visualizers import ChartBuilder, KGVisualizer
from ..exceptions import ExportException

logger = logging.getLogger(__name__)

class SchoolReportGenerator:
    """
    Generates PDF reports for School Analytics (Typst-based)
    """
    def __init__(self):
        # We lazily import to avoid issues if not installed, but here we assume installed
        from mathesis_core.export.typst_wrapper import TypstGenerator
        self.typst_gen = TypstGenerator()
        # Path to the template we just created
        import os
        self.template_path = os.path.join(
            os.path.dirname(__file__), 
            "templates", 
            "school_report.typ"
        )

    async def generate_report(
        self,
        school_data: SchoolData,
        ai_summary: str,
        kg_data: Dict,
        stats: Dict
    ) -> bytes:
        """
        Generate full PDF report using Typst
        """
        try:
            import os
            import shutil
            
            # Prepare Data Context for Typst
            context = {
                "school_name": school_data.school_name,
                "school_code": school_data.school_code,
                "address": school_data.address or "N/A",
                "founding_date": school_data.founding_date or "N/A",
                "ai_summary": ai_summary,
                "curriculum": [
                    {
                        "year": c.year,
                        "grade": c.grade,
                        "subjects": [{"name": s.name} for s in c.subjects]
                    } for c in school_data.curriculum
                ],
                "stats": stats # Placeholder if template uses it
            }
            
            # Output filenames
            # Use /tmp or local dir for generation
            # For this pipeline, we often save to current dir or specific artifact dir
            base_filename = f"report_{school_data.school_code}"
            json_filename = "school_data.json" # As hardcoded in template for now
            pdf_filename = f"{base_filename}.pdf"
            
            # Ensure "school_data.json" matches what the template expects
            # The template says: #let data = json("school_data.json")
            # So we MUST write to "school_data.json" in the SAME directory where we run compile.
            
            # We call compile. The wrapper writes "data.json" corresponding to output path.
            # But the template expects "school_data.json".
            # Let's override the wrapper logic slightly or just conform to wrapper.
            # Wrapper writes: Path(output_path).with_suffix('.json') -> report_123.json
            
            # I should update the template to NOT hardcode "school_data.json" or update wrapper.
            # Updating wrapper is better: pass `data_filename`? 
            # Or simplified: wrapper writes `report_CODE.json`, and we pass that filename to template via CLI?
            # Typst 0.11 supports `--input`.
            
            # FAST FIX: Write `school_data.json` manually here, then call compile.
            # Wrapper logic `compile` was: write json -> typst compile.
            # Let's adjust wrapper usage or just write file here and call raw command?
            # No, user wants module usage.
            
            # Let's Update the Wrapper to support custom data filename or Template to use sys.inputs.
            # BUT I cannot edit wrapper in this turn easily without multiple calls. 
            # I will just write `school_data.json` here manually and call text compile, 
            # OR better: Update the template in the NEXT step to read `report_{code}.json` dynamically? can't.
            
            # Hack: Rename the local json file to `school_data.json` before compile, 
            # or strictly invoke wrapper which writes `report_{code}.json` and fail?
            
            # Let's assume I fix the template to use `sys.inputs`. 
            # Actually, `json("school_data.json")` is what I wrote.
            
            # Correct approach:
            # 1. Write `school_data.json` manually.
            # 2. Call wrapper.compile but suppress its json writing? 
            #    Or wrapper writes `report.json` and I ignore it.
            
            # Let's just implement the logic here cleanly:
            import json
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
                
            # Compile using wrapper's helper for command construction? 
            # The wrapper `compile` method does full execution.
            # I'll let the wrapper write `report_7091234.json` (unused) and I write `school_data.json` (used).
            
            self.typst_gen.compile(self.template_path, context, pdf_filename)
            
            # Clean up JSON
            # if os.path.exists(json_filename): os.remove(json_filename)
            
            # Return bytes
            if os.path.exists(pdf_filename):
                with open(pdf_filename, "rb") as f:
                    return f.read()
            else:
                 raise ExportException("Typst output file not found")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise ExportException(f"Typst generation failed: {e}")
