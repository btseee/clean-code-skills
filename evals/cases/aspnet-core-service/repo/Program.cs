using Microsoft.EntityFrameworkCore;
using ProjectsApi.Data;
using ProjectsApi.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("Default")));
builder.Services.AddScoped<IProjectService, ProjectService>();

var app = builder.Build();

app.MapControllers();
app.Run();
