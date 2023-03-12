using Microsoft.EntityFrameworkCore;

namespace CFA_AutomationUI.Models
{
    [Keyless]
    public class ClockOutVarianceEntry
    {
        public DateTime ShiftDate { get; set; }
        public string ShiftType { get; set; }
        public int ClockOutVariance { get; set; }
    }
}
