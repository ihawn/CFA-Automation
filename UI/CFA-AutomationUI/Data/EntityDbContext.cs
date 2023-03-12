using Microsoft.EntityFrameworkCore;
using CFA_AutomationUI.Models;

namespace CFA_AutomationUI.Data
{
    public class EntityDbContext : DbContext
    {
        private readonly IConfiguration _configuration;

        public EntityDbContext(IConfiguration configuration)
        {
            _configuration = configuration;
        }
        public DbSet<ClockOutVarianceEntry> Customers { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseSqlServer(_configuration.GetValue<string>("ConnectionString"));
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<ClockOutVarianceEntry>(builder =>
            {
                builder.HasNoKey();
                builder.Property(e => e.ShiftDate).HasColumnName("ShiftDate");
                builder.Property(e => e.ShiftType).HasColumnName("ShiftType");
                builder.Property(e => e.ClockOutVariance).HasColumnName("ClockOutVariance");
            });

            modelBuilder.Entity<Role>(builder =>
            {
                builder.HasKey(e => e.Id).HasName("Id");
                builder.Property(e => e.Name).HasColumnName("RoleName");
            });

            modelBuilder.Entity<Employee>(builder =>
            {
                builder.HasKey(e => e.Id).HasName("Id");
                builder.Property(e => e.Name).HasColumnName("Name");
            });

            modelBuilder.Entity<RoleMapping>(builder =>
            {
                builder.HasNoKey();
                builder.Property(e => e.EmployeeId).HasColumnName("EmployeeId");
                builder.Property(e => e.RoleId).HasColumnName("RoleId");
            });
        }
    }
}
