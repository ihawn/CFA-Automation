using CFA_AutomationUI.Models;
using Microsoft.EntityFrameworkCore;

namespace CFA_AutomationUI.Data
{
    public sealed class DataRetriever
    {
        private static DataRetriever instance;
        public static readonly object padlock = new object();
        private readonly IConfiguration config;
        private readonly EntityDbContext db;

        private DataRetriever(IConfiguration configuration)
        {
            config = configuration;
            db = new EntityDbContext(config);
        }

        public static DataRetriever Retriever
        {
            get
            {
                lock(padlock)
                {
                    return instance;
                }
            }
        }

        public static void Initialize(IConfiguration configuration) 
        {
            if(instance == null)
                instance = new DataRetriever(configuration);
        }

        public List<ClockOutVarianceEntry> GetMostRecentClockOutVarianceReport(List<string> roleIds)
        {
            return db.Set<ClockOutVarianceEntry>().FromSqlInterpolated(
                $"EXEC ClockOutVarianceReport {string.Join(",", roleIds)}"
            ).ToList();
        }

        public void SeedEmployees()
        {
            db.Database.ExecuteSqlRaw($"EXEC SeedEmployees");
        }

        public List<Role> GetAllRoles()
        {
            return db.Set<Role>().FromSqlInterpolated($"SELECT * FROM Role ORDER BY RoleName").ToList();
        }

        public List<Employee> GetAllEmployees()
        {
            return db.Set<Employee>().FromSqlInterpolated($"SELECT * FROM Employee ORDER BY Name").ToList();
        }

        public void SetPermission(bool value, string roleId, string employeeId)
        {
            if (value)
                db.Database.ExecuteSqlRaw($"INSERT INTO RoleMappings (RoleId, EmployeeId) Values ('{roleId}', '{employeeId}')");
            else
                db.Database.ExecuteSqlRaw($"DELETE FROM RoleMappings WHERE RoleId = '{roleId}' AND EmployeeId = '{employeeId}'");
        }

        public Dictionary<string, List<string>> GetEmployeeRoles()
        {
            List<RoleMapping> roleMappings = db.Set<RoleMapping>().FromSqlInterpolated($"EXEC GetEmployeeRoles").ToList();
            Dictionary<string, List<string>> employeeRoles = roleMappings
                .GroupBy(rm => rm.EmployeeId)
                .ToDictionary(g => g.Key, g => g.Where(rm => rm.RoleId != null)
                                                  .Select(rm => rm.RoleId)
                                                  .ToList());

            return employeeRoles;
        }
    }
}
