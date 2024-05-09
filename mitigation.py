import dash
from dash import html

mitigation_strategies = {
    # Process
    'IT System Failures': [
        html.P("Establish a comprehensive IT disaster recovery plan and conduct regular system backups."),
        html.P("Implement redundant systems and high-availability solutions to minimize downtime."),
    ],
    'Technological Obsolescence': [
        html.P("Schedule regular technology reviews and establish a replacement cycle aligned with industry standards."),
        html.P("Invest in employee training on new technologies and foster a culture of continuous learning."),
    ],
    'Supplier Count Range': [
        html.P("Conduct periodic reviews of supplier performance and diversify supplier base to mitigate risks."),
        html.P("Develop strategic partnerships with key suppliers to ensure reliable supply chains."),
    ],

    # Organization Structure
    'Labor Strikes': [
        html.P("Foster a work environment that values employee feedback and promotes fair labor practices."),
        html.P("Establish contingency plans to maintain operations during periods of labor unrest."),
    ],
    'Cost Overruns': [
        html.P("Implement stringent budget controls and regular audit mechanisms."),
        html.P("Adopt project management methodologies that emphasize cost control."),
    ],

    # Environment
    'Environmental Regulations': [
        html.P("Stay updated with regulatory changes and ensure compliance through regular audits."),
        html.P("Invest in sustainable practices and technologies that exceed regulatory requirements."),
    ],
    'Natural Disasters': [
        html.P("Develop and regularly update an emergency preparedness and response plan."),
        html.P("Invest in insurance and infrastructure that can withstand environmental risks."),
    ],
    'Regulatory Changes': [
        html.P("Engage with policymakers and industry associations to stay ahead of potential regulatory changes."),
        html.P("Adopt flexible business strategies that can quickly adapt to new regulations."),
    ],
    'Global Pandemic': [
        html.P("Create a pandemic response plan that includes remote working capabilities and health protocols."),
        html.P("Maintain a reserve of essential supplies and diversify production locations to minimize disruptions."),
    ],
    'Market Demand Fluctuations': [
        html.P("Use predictive analytics to understand market trends and adjust production accordingly."),
        html.P("Diversify product offerings to cater to different market segments and reduce reliance on a single product."),
    ],
    'Currency Fluctuations': [
        html.P("Use financial hedging instruments to manage risks related to currency exchange rates."),
        html.P("Diversify revenue streams across different currencies to mitigate potential losses."),
    ],

    # Upstream
    'Political Instability': [
        html.P("Monitor political developments and have contingency plans for rapid response."),
        html.P("Diversify operations across regions to mitigate the impact of political instability in any one area."),
    ],
    'Supplier Delays': [
        html.P("Implement just-in-time inventory systems and establish backup suppliers."),
        html.P("Strengthen supplier relationships and contracts to include delivery guarantees."),
    ],
    'Supply Chain Disruptions': [
        html.P("Develop a resilient supply chain with multiple logistics options."),
        html.P("Invest in supply chain visibility tools for real-time tracking of goods."),
    ],
    'Supplier Financial Instability': [
        html.P("Perform regular financial assessments of suppliers and develop risk profiles."),
        html.P("Secure alternative suppliers for critical components to reduce dependency."),
    ],

    # Downstream
    'Baggage Handling System Failure': [
        html.P("Conduct regular maintenance and simulations to ensure baggage system reliability."),
        html.P("Invest in technology upgrades and staff training for efficient baggage handling operations."),
    ],
}
