using ProjectsApi.Models;

namespace ProjectsApi.Services;

public interface IProjectService
{
    Task<List<Project>> GetActiveProjectsAsync(CancellationToken cancellationToken);
}
