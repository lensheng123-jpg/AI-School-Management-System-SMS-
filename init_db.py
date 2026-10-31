"""
AI-SMS database initializer.
Loads synthetic data from the Excel starter dataset into SQLite.
"""
import sqlite3
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database', 'ai_sms.db')
EXCEL_FILE = os.path.join(BASE_DIR, 'data', 'AI_SMS_Starter_Datasets.xlsx')


def init():
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}\n"
            "Place AI_SMS_Starter_Datasets.xlsx inside the data/ folder."
        )

    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE policies (
            policy_id TEXT PRIMARY KEY,
            school_id TEXT,
            title TEXT,
            version TEXT,
            effective_date TEXT,
            owner_role_id TEXT,
            authority_status TEXT,
            language TEXT,
            source_path TEXT,
            data_origin TEXT
        );

        CREATE TABLE policy_clauses (
            clause_id TEXT PRIMARY KEY,
            policy_id TEXT,
            section TEXT,
            clause_text TEXT,
            authority_status TEXT,
            data_origin TEXT
        );

        CREATE TABLE roles (
            role_id TEXT PRIMARY KEY,
            school_id TEXT,
            role_name TEXT,
            responsibility TEXT,
            consultation_reason TEXT,
            availability TEXT,
            data_origin TEXT
        );

        CREATE TABLE cases (
            case_id TEXT PRIMARY KEY,
            school_id TEXT,
            split TEXT,
            title TEXT,
            category TEXT,
            decision_question TEXT,
            intended_outcome TEXT,
            opened_date TEXT,
            decision_due_date TEXT,
            status TEXT,
            data_origin TEXT
        );

        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            case_id TEXT,
            source_label TEXT,
            source_role_id TEXT,
            recorded_date TEXT,
            evidence_type TEXT,
            verification_status TEXT,
            text TEXT,
            data_origin TEXT
        );

        CREATE TABLE case_policy_links (
            link_id TEXT PRIMARY KEY,
            case_id TEXT,
            policy_id TEXT,
            link_basis TEXT,
            data_origin TEXT
        );

        CREATE TABLE case_analysis (
            analysis_id TEXT PRIMARY KEY,
            case_id TEXT,
            evidence_gap TEXT,
            stakeholder_groups TEXT,
            stakeholder_priorities TEXT,
            potential_conflict TEXT,
            consultation_role_ids TEXT,
            risk_lane TEXT,
            risk_basis TEXT,
            uncertainty_note TEXT,
            review_status TEXT,
            data_origin TEXT
        );

        CREATE TABLE case_options (
            option_id TEXT PRIMARY KEY,
            case_id TEXT,
            option_text TEXT,
            display_order INTEGER,
            rank TEXT,
            benefit TEXT,
            drawback TEXT,
            dependency TEXT,
            short_term_consequence TEXT,
            long_term_consequence TEXT,
            uncertainty TEXT,
            evidence_ids TEXT,
            policy_id TEXT,
            data_origin TEXT
        );

        CREATE TABLE human_decisions (
            decision_id TEXT PRIMARY KEY,
            case_id TEXT,
            selected_option_id TEXT,
            human_decision_text TEXT,
            human_rationale TEXT,
            confirmation_status TEXT,
            decision_date TEXT,
            review_date TEXT,
            outcome_status TEXT,
            outcome_notes TEXT,
            data_origin TEXT
        );
    ''')

    xls = pd.ExcelFile(EXCEL_FILE)

    def load(sheet, table):
        df = pd.read_excel(xls, sheet)
        df.to_sql(table, conn, if_exists='append', index=False)
        print(f"  Loaded {len(df)} rows into {table}")

    print("Loading data...")

    load('Policies', 'policies')
    load('Policy clauses', 'policy_clauses')
    load('Roles', 'roles')

    dev_cases = pd.read_excel(xls, 'Development cases')
    cur_cases = pd.read_excel(xls, 'Current cases')
    all_cases = pd.concat([dev_cases, cur_cases], ignore_index=True)
    all_cases.to_sql('cases', conn, if_exists='append', index=False)
    print(f"  Loaded {len(all_cases)} rows into cases")

    dev_ev = pd.read_excel(xls, 'Development evidence')
    cur_ev = pd.read_excel(xls, 'Current evidence')
    all_ev = pd.concat([dev_ev, cur_ev], ignore_index=True)
    all_ev.to_sql('evidence', conn, if_exists='append', index=False)
    print(f"  Loaded {len(all_ev)} rows into evidence")

    dev_pl = pd.read_excel(xls, 'Development policy links')
    cur_pl = pd.read_excel(xls, 'Current policy links')
    all_pl = pd.concat([dev_pl, cur_pl], ignore_index=True)
    all_pl.to_sql('case_policy_links', conn, if_exists='append', index=False)
    print(f"  Loaded {len(all_pl)} rows into case_policy_links")

    load('Development analysis', 'case_analysis')
    load('Development options', 'case_options')
    load('Human decisions', 'human_decisions')

    conn.commit()
    conn.close()
    print("\nDatabase initialized successfully.")
    print(f"Location: {DATABASE}")


if __name__ == '__main__':
    init()