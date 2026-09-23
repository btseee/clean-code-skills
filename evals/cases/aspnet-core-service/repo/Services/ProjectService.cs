using Microsoft.EntityFrameworkCore;
using ProjectsApi.Data;
using ProjectsApi.Models;

namespace ProjectsApi.Services;

public class ProjectService : IProjectService
{
    private readonly AppDbContext _dbContext;

    public ProjectService(AppDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<List<Project>> GetActiveProjectsAsync(CancellationToken cancellationToken)
    {
        return await _dbContext.Projects
            .AsNoTracking()
            .Where(project => !project.IsArchived)
            .ToListAsync(cancellationToken);
    }
}
