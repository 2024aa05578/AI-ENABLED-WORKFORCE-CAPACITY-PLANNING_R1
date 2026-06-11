# engines.py
import pandas as pd
import numpy as np

class WorkforceCapacityEngine:
    def __init__(self, work_file_path: str, projects_file_path: str):
        self.work_file_path = work_file_path
        self.projects_file_path = projects_file_path
        
    def load_clean_data(self):
        """Loads and prepares structural sheets for ingestion"""
        # Parsing raw projects data
        self.df_projects = pd.read_csv(self.projects_file_path, skiprows=1)
        # Drop columns or metadata headers that lack a Customer identifier
        self.df_projects = self.df_projects.dropna(subset=['Customer'])
        
        # Coerce hours metrics to floats to safeguard analytical pipelines
        hour_cols = ['Per Year Hrs required for PM', 'Total Starup Man Hrs required']
        for col in hour_cols:
            if col in self.df_projects.columns:
                self.df_projects[col] = pd.to_numeric(self.df_projects[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return self.df_projects

    def calculate_bau_baseline(self, product_growth_matrix: dict, regional_attrition: float = 0.08):
        """
        Calculates baseline requirements using historical Active Install Base and Attrition values
        """
        # Default representation mirroring manual workbook benchmarks
        regions = ['North', 'West', 'South', 'East']
        products = ['SP UPS', 'SP Cooling', 'Power Products', 'Power System', 'Industiral Automation']
        
        bau_records = []
        for region in regions:
            for prod in products:
                # Safely capture growth factor mapping variations
                growth_factor = product_growth_matrix.get(prod, {}).get(region, 0.15)
                # Calculating adjusted retention requirements to cover attrition gaps
                attrition_coverage = 1 + regional_attrition
                bau_records.append({
                    'Region': region,
                    'Product Type': prod,
                    'Growth Rate': growth_factor,
                    'Attrition Buffer': attrition_coverage
                })
        return pd.DataFrame(bau_records)

    def extract_project_demand(self):
        """
        Processes project pipelines to determine workload demands 
        and maps them to required engineering headcount hours.
        """
        if not hasattr(self, 'df_projects'):
            self.load_clean_data()
            
        # Group capacity allocations across physical regions and technology profiles
        summary = self.df_projects.groupby(['Region', 'Product Type']).agg({
            'Qty': 'sum',
            'Per Year Hrs required for PM': 'sum',
            'Total Starup Man Hrs required': 'sum'
        }).reset_index()
        
        # Standard working matrix: 1 Service Engineer (SE) = ~2000 available operational hours/year
        summary['SR Required PM'] = summary['Per Year Hrs required for PM'] / 2000.0
        summary['SR Required Startup'] = summary['Total Starup Man Hrs required'] / 2000.0
        summary['Total Project Headcount Needed'] = summary['SR Required PM'] + summary['SR Required Startup']
        
        return summary

    def optimize_allocations(self, product_growth_matrix: dict, standard_capacity: float = 2000.0):
        """
        Combines operational vectors to provide structural balancing recommendations.
        """
        proj_demand = self.extract_project_demand()
        
        # Generate baseline locations for mapping optimizations
        optimization_matrix = []
        for idx, row in proj_demand.iterrows():
            reg = row['Region']
            prod = row['Product Type']
            proj_se = row['Total Headcount Needed']
            
            # Simple heuristic allocation balancing regional distribution dynamics
            recommended_action = "Maintain Current Hub"
            if proj_se > 15.0:
                recommended_action = "Establish Dedicated On-Site Support Hub"
            elif proj_se > 5.0 and reg != 'South': # Bangalore is South Region baseline
                recommended_action = "Deploy Regional Field Group"
            elif proj_se > 2.0:
                recommended_action = "Cross-Train Local Assets"
                
            optimization_matrix.append({
                'Region': reg,
                'Product Domain': prod,
                'Project Headcount Demand': round(proj_se, 2),
                'Strategic Location Guidance': recommended_action
            })
            
        return pd.DataFrame(optimization_matrix)
