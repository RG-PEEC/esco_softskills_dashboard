import pandas as pd
import ast

data_df = pd.read_csv("data/volunteer_activities_transversal_skills_predictions_new_prompt_new_no_batch_new.csv",
                      converters={"y_pred_detailed": ast.literal_eval, "Y": ast.literal_eval,
                                  "y_pred": ast.literal_eval})

person_1 = [
    "assume responsibility",
    "meet commitments",
    "demonstrate trustworthiness",
    "manage time",
    "cope with stress",
    "manage frustration",
    "maintain psychological well-being",
    "exercise self-reflection",
    "think critically",
    "solve problems",
    "identify problems",
    "think analytically",
    "critically evaluate information and its sources ",
    "work in teams",
    "show empathy",
    "accept criticism and guidance",
    "resolve conflicts",
    "negotiate compromises",
    "address an audience",
    "organise information, objects and resources",
    "express yourself creatively",
    "adapt to change",
    "cope with uncertainty",
    "demonstrate willingness to learn",
    "keep an open mind",
    "respect the diversity of cultural values and norms",
    "exercise rights and responsibilities",
    "promote the principles of democracy and rule of law",
    "evaluate environmental impact of personal behaviour",
    "think creatively",
    "think innovately",
    "show initiative"
]

person_2 = [
    "show determination",
    "show commitment",
    "work efficiently",
    "attend to detail",
    "plan ",
    "maintain concentration for long periods",
    "organise information, objects and resources",
    "delegate responsibilities",
    "manage quality",
    "comply with regulations",
    "report facts",
    "apply digital security measures",
    "use equipment, tools or technology with precision",
    "apply hygiene standards",
    "respect confidentiality obligations"
]

person_3 = [
    "demonstrate curiosity",
    "demonstrate willingness to learn",
    "think creatively",
    "think innovately",
    "improvise",
    "build networks",
    "show entrepreneurial spirit",
    "motivate others",
    "express yourself creatively",
    "build team spirit",
    "promote ideas, products, services ",
    "create digital content",
    "conduct web searches",
    "apply basic programming skills",
    "operate digital hardware",
    "use communication and collaboration software",
    "manage digital identity"
]

person_4 = [
    "accept criticism and guidance",
    "show empathy",
    "demonstrate intercultural competence",
    "moderate a discussion",
    "address an audience",
    "negotiate compromises",
    "resolve conflicts",
    "demonstrate loyalty",
    "demonstrate trustworthiness",
    "participate actively in civic life",
    "promote the principles of democracy and rule of law",
    "respect the diversity of cultural values and norms",
    "appreciate diverse cultural and artistic expression",
    "engage others in environment friendly behaviours"
]

person_5 = [
    "adjust to physical demands",
    "maintain physical fitness",
    "cope with uncertainty",
    "react to physical changes or hazards",
    "manage chronic health conditions",
    "make an informed use of the health-care system",
    "apply knowledge of science, technology and engineering",
    "apply knowledge of philosophy, ethics and religion",
    "apply knowledge of social sciences and humanities",
    "evaluate environmental impact of personal behaviour",
    "adopt ways to reduce pollution",
    "adopt ways to reduce negative impact of consumption",
    "adopt ways to foster biodiversity and animal welfare",
    "protect the health of others",
    "demonstrate awareness of health risks "
]

persons = [person_1, person_2, person_3, person_4, person_5]