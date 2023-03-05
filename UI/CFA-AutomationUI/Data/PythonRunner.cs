using System.Diagnostics;

namespace CFA_AutomationUI.Data
{
    public static class PythonRunner
    {
        public static void RunClockInCrawlerJob(IConfiguration config, DateTime fromDate, DateTime thruDate, string username, string password)
        {
            string pythonInterpreterPath = config.GetValue<string>("PythonInterpreterPath");
            string pythonScriptPath = config.GetValue<string>("PythonScriptPath");

            ProcessStartInfo startInfo = new ProcessStartInfo();
            startInfo.FileName = pythonInterpreterPath;
            startInfo.Arguments = pythonScriptPath 
                + $" {fromDate.ToString("M/d/yyyy")} {thruDate.ToString("M/d/yyyy")} {username} {password}";
            startInfo.RedirectStandardOutput = true;
            startInfo.UseShellExecute = false;

            using (Process process = new Process())
            {
                process.StartInfo = startInfo;
                process.Start();
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
            }
        }
    }
}
