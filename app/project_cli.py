from app.agent.project_reasoner import reason_about_project
from app.ai.reasoner import analyze_with_ai

def analyze(project_root, error):
    reasoning = reason_about_project(error, project_root)
    return reasoning, analyze_with_ai(reasoning)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FixPilot project-aware analysis")
    parser.add_argument("error")
    parser.add_argument("--project", default=".")
    args = parser.parse_args()

    reasoning, ai = analyze(args.project, args.error)
    print("PROJECT CONTEXT")
    print(reasoning["project_summary"])
    print("\nAI ANALYSIS")
    print(ai)
