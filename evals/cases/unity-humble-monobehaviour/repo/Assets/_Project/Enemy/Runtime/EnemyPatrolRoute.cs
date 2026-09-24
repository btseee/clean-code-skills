using UnityEngine;

public class EnemyPatrolRoute
{
    private readonly Transform _mover;

    public EnemyPatrolRoute(Transform mover)
    {
        _mover = mover;
    }

    public void Advance(float deltaTime)
    {
        _mover.Translate(Vector3.forward * deltaTime);
    }
}
