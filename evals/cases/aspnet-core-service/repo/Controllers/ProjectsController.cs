using Microsoft.AspNetCore.Mvc;
using ProjectsApi.Services;

namespace ProjectsApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProjectsController : ControllerBase
{
    private readonly IProjectService _projectService;

    public ProjectsController(IProjectService projectService)
    {
        _projectService = projectService;
    }

    [HttpGet]
    public async Task<IActionResult> GetActive(CancellationToken cancellationToken)
    {
        var projects = await _projectService.GetActiveProjectsAsync(cancellationToken);
        return Ok(projects);
    }
}
