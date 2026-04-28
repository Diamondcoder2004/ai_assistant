import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('analysis_summary.csv')

plt.figure(figsize=(12,8))
sns.barplot(data=df, x=df.columns[0], y='high_accuracy_percent')
plt.title('High Accuracy Percent by Category')
plt.xlabel('Category')
plt.ylabel('High Accuracy Percent')
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.3)
plt.tight_layout()
plt.savefig('accuracy_barplot.png')
plt.close()

plt.figure(figsize=(10,6))
sns.histplot(data=df, x='mean_overall_score', bins=10)
plt.title('Histogram of Mean Overall Score')
plt.xlabel('Mean Overall Score')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig('score_histogram.png')
plt.close()
