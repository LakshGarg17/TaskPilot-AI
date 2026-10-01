import ast
import math
import statistics
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field
from app.agents.tools.base import BaseTool, ToolResult

class CalculatorInput(BaseModel):
    expression: str = Field(..., description="Mathematical or statistical expression, e.g., '150000 / 3' or 'mean([100, 150, 200])'")

# Safe allowed math operations
SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "mean": statistics.mean,
    "median": statistics.median,
    "variance": statistics.variance,
    "stdev": statistics.stdev,
}

class SafeEvalVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise ValueError(f"Disallowed expression node: {node.__class__.__name__}")

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Disallowed constant type: {type(node.value)}")

    def visit_List(self, node: ast.List):
        return [self.visit(elt) for elt in node.elts]

    def visit_Tuple(self, node: ast.Tuple):
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Disallowed unary operator: {node.op.__class__.__name__}")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        elif isinstance(op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("Integer division by zero")
            return left // right
        elif isinstance(op, ast.Mod):
            return left % right
        elif isinstance(op, ast.Pow):
            if abs(right) > 100:
                raise ValueError("Exponent too large")
            return left ** right
        raise ValueError(f"Disallowed binary operator: {op.__class__.__name__}")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct named functions from whitelist are allowed")
        func_name = node.func.id
        if func_name not in SAFE_FUNCS:
            raise ValueError(f"Function '{func_name}' is not allowed")
        args = [self.visit(arg) for arg in node.args]
        return SAFE_FUNCS[func_name](*args)

def safe_calculate(expr: str) -> Union[int, float, List[Any]]:
    expr_clean = expr.strip()
    parsed = ast.parse(expr_clean, mode='eval')
    evaluator = SafeEvalVisitor()
    return evaluator.visit(parsed)

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Safely evaluates mathematical and statistical expressions over numbers, lists, or datasets without eval/exec."
    risk_level = "LOW"
    input_schema = CalculatorInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        try:
            validated = self.validate_inputs(inputs)
            result = safe_calculate(validated.expression)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                formatted = int(result)
            elif isinstance(result, float):
                formatted = round(result, 4)
            else:
                formatted = result

            return ToolResult(
                ok=True,
                data={"result": formatted, "expression": validated.expression},
                summary=f"Calculated {validated.expression} = {formatted}"
            )
        except Exception as e:
            return ToolResult(
                ok=False,
                error=f"Calculation error: {str(e)}",
                summary=f"Failed to calculate expression: {inputs.get('expression', '')}"
            )
