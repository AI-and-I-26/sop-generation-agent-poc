Here's the complete business case, pulled directly from your HubStor Master Report data. Let me walk you through the key findings:

📊 What Your Data Shows
Your HubStor subscription covers 1,041.7 TiB of data across 5 Azure regions, costing $35,523/month ($426K/year). The critical insight is the storage tier breakdown:
TierVolume% of TotalStandard/Hot15.2 TiB1.4%Cool161.7 TiB15.5%Archive862 TiB82.8%
Archive is dominant — and this is where the massive saving comes from.

💰 Cost Comparison: Azure HubStor → AWS S3
Azure HubStorAWS S3SavingArchive (862 TiB)~$22K/mo~$870/mo96% cheaperCool (162 TiB)~$5.3K/mo~$2.1K/mo60% cheaperStandard/Hot (15 TiB)~$690/mo~$360/mo~48% cheaperTotal/month$35,523~$8,100~$27,400 savingAnnual$426K~$97K~$329K saved ✅
This far exceeds your $100K/year target — it's over 3× that target.
The reason HubStor is so expensive isn't just storage — it charges an ~34% management fee on top of Azure blob rates. AWS S3 has no such platform fee.

🏗️ Architecture: How Sites Connect to S3
The answer to your connectivity question is AWS S3 File Gateway:

A lightweight VM (VMware/Hyper-V) deployed at each site
Presents NFS or SMB shares to local applications — same experience as today
Files written to the share are automatically uploaded to S3
Retrieval works the same way — gateway fetches from S3 transparently
No gateway license fee — you pay only EC2 compute for the VM (~$100/mo per site)
One gateway VM per site can handle all connectors at that site (replacing HubStor agents)

Region mapping preserves data residency — UK data goes to eu-west-2 (London), German data to eu-central-1 (Frankfurt), US data to us-east-1 / us-west-2. No GDPR issues introduced.

🚀 Migration Cost & Payback
The one-time migration cost is approximately $12K, dominated by:

Azure egress fees (~$9K to get 1,042 TiB out of Azure)
AWS DataSync service fees (~$13K — tool that automates the transfer)
Labor for setup, testing, validation

AWS ingress is completely free — no charge to receive data into S3.
Payback period: less than 1 month of savings covers the entire migration cost. Year 1 net saving after migration cost is ~$317K.

The Excel file has 5 sheets: Executive Summary, detailed Cost Comparison model (with blue input cells you can adjust), Migration Plan & Costs, Architecture & Connectivity reference, and a full 36-month financial model.
