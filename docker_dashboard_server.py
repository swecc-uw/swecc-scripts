import os
from flask import Flask, render_template_string, request
import json
from datetime import datetime
import pandas as pd
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<!-- [Previous head and style sections remain the same] -->

<head>
  <title>Docker Stats Dashboard</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
      background-color: #f5f5f5;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
    }

    .card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .charts-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 30px;
    }

    .chart-container {
      height: 250px;
      margin-bottom: 20px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .metric {
      padding: 15px;
      border-radius: 8px;
      background: #f8f9fa;
    }

    .metric h3 {
      margin: 0 0 10px 0;
      color: #333;
    }

    .metric p {
      margin: 5px 0;
    }

    .refresh-button {
      background: #007bff;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      margin-bottom: 20px;
    }

    .refresh-button:hover {
      background: #0056b3;
    }

    .last-update {
      color: #666;
      margin-bottom: 20px;
    }

    .controls {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 20px;
    }

    .line-count {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .line-count input {
      width: 100px;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }

    .line-count label {
      color: #666;
    }
  </style>
</head>

<body>
  <div class="container">
    <h1>Docker Container Stats Dashboard</h1>
    <div class="controls">
      <form action="/" method="get" class="line-count">
        <label for="lines">Number of lines:</label>
        <input type="number" id="lines" name="lines" value="{{ line_count }}" min="1">
        <button type="submit" class="refresh-button">Refresh Data</button>
      </form>
    </div>
    <p class="last-update">Last updated: {{ last_update }}</p>

    <!-- [Rest of the template remains the same] -->
    {% for container in containers %}
    <div class="card">
      <h2>{{ container.name }}</h2>
      <div class="stats-grid">
        <div class="metric">
          <h3>CPU Usage</h3>
          <p>Current: {{ container.current_cpu }}%</p>
          <p>Average: {{ container.avg_cpu }}%</p>
        </div>
        <div class="metric">
          <h3>Memory Usage</h3>
          <p>Current: {{ container.current_memory.usage }} / {{ container.current_memory.limit }}</p>
          <p>Usage (MB): {{ container.current_memory_mb }} MB</p>
          <p>Limit (MB): {{ container.memory_limit_mb }} MB</p>
          <p>Percentage: {{ container.current_memory.percent }}</p>
        </div>
        <div class="metric">
          <h3>Network I/O</h3>
          <p>Input: {{ container.current_network.input }}</p>
          <p>Output: {{ container.current_network.output }}</p>
        </div>
      </div>
      <div class="charts-grid">
        <div class="chart-container">
          <canvas id="cpuChart{{ loop.index }}"></canvas>
        </div>
        <div class="chart-container">
          <canvas id="memChart{{ loop.index }}"></canvas>
        </div>
        <div class="chart-container">
          <canvas id="netChart{{ loop.index }}"></canvas>
        </div>
        <div class="chart-container">
          <canvas id="blockChart{{ loop.index }}"></canvas>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>


  <script>
    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          position: 'left'
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    };

    {% for container in containers %}
    // CPU chart
    new Chart(document.getElementById('cpuChart{{ loop.index }}').getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ container.timestamps | tojson }},
      datasets: [{
        label: 'CPU Usage (%)',
        data: {{ container.cpu_history | tojson }},
      borderColor: '#007bff',
      tension: 0.1
                }]
            },
      options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start'
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          beginAtZero: true,
          title: {
            display: true,
            text: 'CPU %',
            padding: { top: 10, bottom: 10 }
          }
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }});

    // memory chart
    new Chart(document.getElementById('memChart{{ loop.index }}').getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ container.timestamps | tojson }},
      datasets: [{
        label: 'Memory Usage (%)',
        data: {{ container.memory_history | tojson }},
      borderColor: '#28a745',
      tension: 0.1,
      yAxisID: 'percentage'
                }, {
        label: 'Memory Usage (MB)',
        data: {{ container.memory_mb_history | tojson }},
      borderColor: '#20c997',
      tension: 0.1,
      yAxisID: 'megabytes'
                }]
            },
      options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start'
        }
      },
      scales: {
        percentage: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: {
            drawOnChartArea: true
          },
          title: {
            display: true,
            text: 'Memory %',
            padding: { top: 10, bottom: 10 }
          }
        },
        megabytes: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: {
            drawOnChartArea: false
          },
          title: {
            display: true,
            text: 'Memory MB',
            padding: { top: 10, bottom: 10 }
          }
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }});

    // network I/O chart
    new Chart(document.getElementById('netChart{{ loop.index }}').getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ container.timestamps | tojson }},
      datasets: [{
        label: 'Network Input',
        data: {{ container.net_in_history | tojson }},
      borderColor: '#dc3545',
      tension: 0.1
                }, {
        label: 'Network Output',
        data: {{ container.net_out_history | tojson }},
      borderColor: '#fd7e14',
      tension: 0.1
                }]
            },
      options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start'
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          beginAtZero: true,
          title: {
            display: true,
            text: 'Network I/O (MB)',
            padding: { top: 10, bottom: 10 }
          }
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }});

    // block I/O chart
    new Chart(document.getElementById('blockChart{{ loop.index }}').getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ container.timestamps | tojson }},
      datasets: [{
        label: 'Block Input',
        data: {{ container.block_in_history | tojson }},
      borderColor: '#6610f2',
      tension: 0.1
                }, {
        label: 'Block Output',
        data: {{ container.block_out_history | tojson }},
      borderColor: '#20c997',
      tension: 0.1
                }]
            },
      options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start'
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          beginAtZero: true,
          title: {
            display: true,
            text: 'Block I/O (MB)',
            padding: { top: 10, bottom: 10 }
          }
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }});
    {% endfor %}
  </script>
</body>
</html>
"""


def convert_to_mb(size_str):
    size_str = size_str.upper()
    number = float("".join(filter(lambda x: x.isdigit() or x == ".", size_str)))

    if "KIB" in size_str or "KB" in size_str:
        return number / 1024
    elif "MIB" in size_str or "MB" in size_str:
        return number
    elif "GIB" in size_str or "GB" in size_str:
        return number * 1024
    return number


def parse_stats_file(file_path):
    data = []
    with open(file_path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def process_container_data(data):
    df = pd.DataFrame(data)

    containers = []
    for name, group in df.groupby("name"):
        group = group.sort_values("timestamp")

        cpu_values = [float(str(cpu).rstrip("%")) for cpu in group["cpu_percent"]]

        # memory
        memory_values = [
            float(str(mem["percent"]).rstrip("%")) for mem in group["memory"]
        ]
        memory_mb_values = [convert_to_mb(mem["usage"]) for mem in group["memory"]]

        # network I/O
        net_in_values = [convert_to_mb(net["input"]) for net in group["network"]]
        net_out_values = [convert_to_mb(net["output"]) for net in group["network"]]

        # block I/O
        block_in_values = [convert_to_mb(block["input"]) for block in group["block_io"]]
        block_out_values = [
            convert_to_mb(block["output"]) for block in group["block_io"]
        ]

        timestamps = [
            datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
            for ts in group["timestamp"]
        ]

        latest = group.iloc[-1]

        current_memory_mb = convert_to_mb(latest["memory"]["usage"])
        memory_limit_mb = convert_to_mb(latest["memory"]["limit"])

        containers.append(
            {
                "name": name,
                "current_cpu": latest["cpu_percent"],
                "avg_cpu": f"{sum(cpu_values) / len(cpu_values):.2f}",
                "current_memory": latest["memory"],
                "current_memory_mb": f"{current_memory_mb:.2f}",
                "memory_limit_mb": f"{memory_limit_mb:.2f}",
                "current_network": latest["network"],
                "timestamps": timestamps,
                "cpu_history": cpu_values,
                "memory_history": memory_values,
                "memory_mb_history": memory_mb_values,
                "net_in_history": net_in_values,
                "net_out_history": net_out_values,
                "block_in_history": block_in_values,
                "block_out_history": block_out_values,
            }
        )

    containers.sort(key=lambda x: x["name"], reverse=True)

    return containers


last_update = None


def fetch_remote_logs(remote_alias, remote_path, line_count=None):
    """Fetch logs from remote server using SSH and tail"""
    try:
        if line_count:
            command = f"ssh {remote_alias} 'sudo tail -n {line_count} {remote_path}'"
        else:
            command = f"ssh {remote_alias} 'sudo cat {remote_path}'"

        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error fetching logs: {result.stderr}")
            return []

        data = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                    continue

        return data
    except Exception as e:
        print(f"Error executing SSH command: {e}")
        return []


@app.route("/")
def dashboard():
    remote_alias = "swecc-server"
    remote_path = "/var/log/docker-stats.log"

    line_count = request.args.get("lines", type=int)

    data = fetch_remote_logs(remote_alias, remote_path, line_count)

    if not data:
        return "Error: Could not fetch log data from remote server.", 500

    containers = process_container_data(data)

    return render_template_string(
        HTML_TEMPLATE,
        containers=containers,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        line_count=line_count or "",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
